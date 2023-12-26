import logging
from functools import lru_cache

from croniter import croniter
from croniter.croniter import CroniterError
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.urls import reverse
from jelastic import Jelastic
from jelastic.api.exceptions import JelasticApiError

import json
from netbox.config import get_config
from netbox.models import PrimaryModel, ChangeLoggedModel
from .constants import *

__all__ = ("NetBoxConfiguration", "NetBoxDBBackup")

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
        validators=[MinLengthValidator(5)],
        verbose_name="Environment Name",
    )

    env_name_storage = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        validators=[MinLengthValidator(5)],
        verbose_name="Environment Name Storage",
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

        if self.env_name_storage:
            try:
                # Ensure the provided env_name_storage exists
                self._jelastic().environment.Control.GetEnvInfo(
                    env_name=self.env_name_storage
                )
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
    def _env(self, env_name):
        """
        Return information about the environment.
        """
        try:
            return self._jelastic().environment.Control.GetEnvInfo(
                env_name=env_name,
            )
        except JelasticApiError as e:
            logger.error(e)
            return {}

    def _env_info(self, env_name):
        """
        Return information about the environment.
        """
        return self._env(env_name).get("env", {})

    def env_info(self):
        return self._env_info(self.env_name)

    def env_storage_info(self):
        return self._env_info(self.env_name_storage)

    def _env_node_groups(self, env_name):
        """
        Return information about the environment.
        """
        node_groups = sorted(
            self._env(env_name).get("nodeGroups", {}),
            key=lambda x: x.get("displayName", x.get("name")),
        )

        # For each node group, add the related nodes
        for node_group in node_groups:
            node_group["node"] = self.env_nodes(
                env_name, node_group["name"], is_master=True
            )

        return node_groups

    def env_node_groups(self):
        return self._env_node_groups(self.env_name)

    def env_storage_node_groups(self):
        return self._env_node_groups(self.env_name_storage)

    def env_nodes(self, env_name, node_group, is_master=True):
        """
        Return information about the environment nodes.

        :param node_group: The node group to filter by.
        :param is_master: Whether to filter by master nodes.
        """
        nodes = self._env(env_name).get("nodes", {})
        group_nodes = []
        for node in nodes:
            if node.get("nodeGroup") == node_group:
                if is_master and node.get("ismaster"):
                    # Master can only be one
                    return node

                group_nodes.append(node)

        return group_nodes

    def env_node(self, env_name, node_id):
        """
        Return information about the environment node.
        """
        node_id = int(node_id)

        nodes = self._env(env_name).get("nodes", {})
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
                self.restart_node_group(node_group=group_name)

    def restart_node_group(self, node_group):
        """
        Restart the node group.
        """
        self._jelastic().environment.Control.RestartNodes(
            env_name=self.env_name,
            node_group=node_group,
        )


class NetBoxDBBackup(ChangeLoggedModel):
    netbox_env = models.ForeignKey(
        to="netbox_cloud_pilot.NetBoxConfiguration",
        on_delete=models.CASCADE,
        related_name="db_backups",
        verbose_name="NetBox Environment",
    )

    crontab = models.CharField(
        max_length=255,
        help_text=(
            "Crontab expression for the backup schedule."
            "See <a href='https://crontab.guru/' target='_blank'>crontab.guru</a> for more information."
        ),
        default="@daily",
    )

    keep_backups = models.PositiveIntegerField(
        default=1,
        help_text="Number of newest backups to keep during rotation.",
    )

    class Meta:
        verbose_name = "NetBox DB Backup"
        verbose_name_plural = "NetBox DB Backups"

    def get_absolute_url(self):
        return reverse("plugins:netbox_cloud_pilot:netboxdbbackup", args=[self.pk])

    def __str__(self):
        return self.crontab

    def clean(self):
        super().clean()

        if self.__class__.objects.exists() and not self.pk:
            raise ValidationError("There can only be one NetBoxDBBackup instance.")

        # Ensure netbox_env has a storage env connected before proceeding
        if not self.netbox_env.env_name_storage:
            raise ValidationError(
                {
                    "netbox_env": "Add a backup storage environment to the NetBoxConfiguration instance."
                }
            )

        if self.keep_backups > 30:
            raise ValidationError(
                {"keep_backups": "The maximum number of backups to keep is 30."}
            )

        if self.keep_backups < 1:
            raise ValidationError(
                {"keep_backups": "The minimum number of backups to keep is 1."}
            )

        try:
            croniter(self.crontab)
        except CroniterError as e:
            raise ValidationError({"crontab": e})

    @property
    def cron(self):
        return ' '.join(croniter(self.crontab).expressions)

    def install_addon(self, app_id="db-backup", settings=None):
        """
        Installs the Database backup/restore addon on the PostgreSQL application.
        """
        # Check if the addon is already installed
        jc = self.netbox_env._jelastic()
        addons = jc.marketplace.App.GetAddonList(
            envName=self.netbox_env.env_name,
            node_group=NODE_GROUP_SQLDB,
            search={'nodeType': 'postgresql', 'app_id': app_id},
        ).get('apps', [])

        addon = None

        for app in addons:
            if app.get('app_id') == app_id and app.get('isInstalled'):
                addon = app
                break

        if addon is None:
            # Install the addon
            jc.marketplace.App.InstallAddon(
                env_name=self.netbox_env.env_name,
                app_id=app_id,
                node_group=NODE_GROUP_SQLDB,
                settings=settings
            )
        else:
            jc.marketplace.Installation.ExecuteAction(
                app_unique_name=addon.get('uniqueName'),
                action='configure',
                params=settings
            )

    def uninstall_addon(self, app_id='db-backup'):
        # Check if the addon is already installed
        jc = self.netbox_env._jelastic()
        addons = jc.marketplace.App.GetAddonList(
            envName=self.netbox_env.env_name,
            node_group=NODE_GROUP_SQLDB,
            search={'nodeType': 'postgresql', 'app_id': app_id},
        ).get('apps', [])

        db_backup_addon = None

        for addon in addons:
            if addon.get('app_id') == app_id:
                if not addon.get('isInstalled'):
                    return addon
                db_backup_addon = addon
                break

        # Get environment info
        env_info = self.netbox_env.env_info()

        jc.marketplace.Installation.Uninstall(
            app_unique_name=db_backup_addon.get('uniqueName'),
            target_app_id=env_info.get('appid'),
            app_template_id=app_id
        )

    def save(self, *args, **kwargs):
        # Install the addon
        self.install_addon(settings={
            'scheduleType': 3,
            'cronTime': self.cron,
            'storageName': self.netbox_env.env_name_storage,
            'backupCount': self.keep_backups,
            'dbuser': 'webadmin',
            'dbpass': self.netbox_env._env_var('DB_PASSWORD'),
        })

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Uninstall the addon
        self.uninstall_addon()

        super().delete(*args, **kwargs)
