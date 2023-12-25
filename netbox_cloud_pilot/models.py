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
        return self.env_info().get("displayName", self.env_name)

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

        # Ensure the provided env_name exists
        try:
            self._env()
        except Exception as e:
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
        return sorted(
            self._env().get("nodeGroups", {}),
            key=lambda x: x.get("displayName", x.get("name")),
        )

    def _env_vars(self, variables):
        """
        Return a dictionary of environment variables for the environment.
        """
        var = {}
        container_var = self._env_var_by_group(NODE_GROUP_CP).get('object', {})
        for key in variables:
            var[key] = getattr(get_config(), key, container_var.get(key, ""))

        return var

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
        config = {key: {} for key in NETBOX_SETTINGS.keys()}

        for key, value in NETBOX_SETTINGS.items():
            config[key].update(self._env_vars(value))

        return config

    @property
    def admin_url(self):
        return JELASTIC_API
