import json
import logging
from functools import lru_cache

from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.urls import reverse
from jelastic import Jelastic
from jelastic.api.exceptions import JelasticApiError

from netbox.config import get_config
from netbox.models import PrimaryModel
from .constants import *

__all__ = ("NetBoxConfiguration",)

logger = logging.getLogger(__name__)


class NetBoxConfiguration(PrimaryModel):
    """
    NetBoxConfig is a model that represents the configuration of NetBox.
    """

    key = models.CharField(
        max_length=255, unique=True, validators=[MinLengthValidator(40)]
    )

    env_name = models.CharField(
        max_length=255,
        unique=True,
        validators=[MinLengthValidator(1)],
        verbose_name="Environment Name",
    )

    class Meta:
        verbose_name = "NetBox Configuration"
        verbose_name_plural = "NetBox Configurations"

    def __str__(self):
        return self.env_name

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloud_pilot:netboxconfiguration", args=[self.pk])

    def clean(self):
        if self.__class__.objects.exists() and not self.pk:
            raise ValidationError("There can only be one NetBoxConfiguration instance.")

        # Clear any cached values from lru_cache
        self._env.cache_clear()
        self._env_var_by_group.cache_clear()

        # Environment name must not contain dots
        if "." in self.env_name:
            raise ValidationError("Environment name must not contain dots.")

        try:
            # Ensure the provided env_name exists
            self._jelastic().environment.Control.GetEnvInfo(env_name=self.env_name)
        except JelasticApiError as e:
            raise ValidationError(e)

    def _jelastic(self):
        """
        Return a Jelastic instance for the environment.
        """
        return Jelastic(
            base_url=JELASTIC_API,
            token=self.key,
        )

    @lru_cache(maxsize=128)
    def _env_var_by_group(self, node_group):
        """
        Return a dictionary of environment variables for the environment.
        """
        try:
            return self._jelastic().environment.Control.GetContainerEnvVarsByGroup(
                env_name=self.env_name,
                node_group=node_group,
            )
        except JelasticApiError as e:
            logger.error(e)
            return {}

    @lru_cache(maxsize=1)
    def _env(self):
        """
        Return information about the environment.
        """
        try:
            return self._jelastic().environment.Control.GetEnvInfo(
                env_name=self.env_name,
            )
        except JelasticApiError as e:
            logger.error(e)
            return {}

    def env_info(self):
        """
        Return information about the environment.
        """
        return self._env().get("env", {})

    def env_node_groups(self):
        """
        Return information about the environment.
        """
        node_groups = sorted(
            self._env().get("nodeGroups", {}),
            key=lambda x: x.get("displayName", x.get("name")),
        )

        # For each node group, add the related nodes
        for node_group in node_groups:
            node_group["node"] = self.env_nodes(node_group["name"], is_master=True)

        return node_groups

    def env_nodes(self, node_group, is_master=True):
        """
        Return information about the environment nodes.

        :param node_group: The node group to filter by.
        :param is_master: Whether to filter by master nodes.
        """
        nodes = self._env().get("nodes", {})
        group_nodes = []
        for node in nodes:
            if node.get("nodeGroup") == node_group:
                if is_master and node.get("ismaster"):
                    # Master can only be one
                    return node

                group_nodes.append(node)

        return group_nodes

    def env_node(self, node_id):
        """
        Return information about the environment node.
        """
        node_id = int(node_id)

        nodes = self._env().get("nodes", {})
        for node in nodes:
            if node.get("id") == node_id:
                return node

        return {}

    def _env_vars(self, variables):
        """
        Return a dictionary of environment variables for the environment.
        """
        var = {}
        for variable in variables:
            var[variable] = self._env_var(variable)

        return var

    def _env_var(self, variable):
        """
        Returns the value of a single environment variable for the environment.
        """
        container_var = self._env_var_by_group(NODE_GROUP_CP).get("object", {})
        return getattr(get_config(), variable, container_var.get(variable, ""))

    @property
    def netbox_admin(self):
        """
        Return the administration credentials for NetBox.
        """
        var = self._env_vars(NETBOX_SUPERUSER_SETTINGS)
        # Get ext domains or domain from env_info and merge with var
        ext_domains = self.env_info().get("extdomains", [])
        ssl_state = self.env_info().get("sslstate", False)
        scheme = "https" if ssl_state else "http"

        if ext_domains:
            var["url"] = f"{scheme}://{ext_domains[0]}"
        else:
            domain = self.env_info().get("domain", "")
            var["url"] = f"{scheme}://{domain}"

        return var

    @property
    def netbox_settings(self):
        """
        Return the environment variable for the `NODE_GROUP_CP` node group.
        """
        config = {}

        for section, settings in NETBOX_SETTINGS.items():
            config[section] = []
            for setting in settings:
                for key, value in setting.items():
                    config[section].append(
                        {key: {**value, "initial": self._env_var(key)}}
                    )

        return config

    @property
    def admin_url(self):
        return JELASTIC_API

    def read_node_log(self, node_id, path="/var/log/run.log"):
        return (
            self._jelastic()
            .environment.Control.ReadLog(
                env_name=self.env_name,
                node_id=node_id,
                path=path,
            )
            .get("body", "")
        )

    def apply_settings(self, data):
        """
        Apply the settings to the environment.
        """
        # Pop any values that are not set in the data
        remove_data = []
        for key, value in data.items():
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass

            if not value:
                remove_data.append(key)

        for key in remove_data:
            data.pop(key)

        # Find all NetBox node groups that starts with `cp`
        node_groups = self.env_node_groups()

        for node_group in node_groups:
            group_name = node_group.get("name")

            if group_name.startswith("cp"):
                self._jelastic().environment.Control.RemoveContainerEnvVars(
                    env_name=self.env_name, node_group=group_name, vars=remove_data
                )

                self._jelastic().environment.Control.AddContainerEnvVars(
                    env_name=self.env_name,
                    node_group=group_name,
                    vars=data,
                )

                # Restart node
                self._jelastic().environment.Control.RestartNodes(
                    env_name=self.env_name,
                    node_group=group_name,
                )
