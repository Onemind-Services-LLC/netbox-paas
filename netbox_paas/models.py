import ast
import json
import logging
import os
import re
from datetime import datetime
from functools import lru_cache

from croniter import croniter
from croniter.croniter import CroniterError
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from django.urls import reverse
from jelastic.api.exceptions import JelasticApiError
from netbox.models import ChangeLoggedModel, PrimaryModel
from netbox.models.features import JobsMixin

from .constants import (
    NETBOX_SUPERUSER_SETTINGS,
    NETBOX_SETTINGS,
    NODE_GROUP_SQLDB,
    NODE_GROUP_CP,
)
from .paas import *

__all__ = ("NetBoxConfiguration", "NetBoxDBBackup")

logger = logging.getLogger(__name__)


class NetBoxConfiguration(JobsMixin, PrimaryModel):
    """
    NetBoxConfig is a model that represents the configuration of NetBox.
    """

    key = models.CharField(max_length=255, unique=True, validators=[MinLengthValidator(40)])

    env_name_storage = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        validators=[MinLengthValidator(5)],
        verbose_name="Environment Name Storage",
    )

    license = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(40), MaxLengthValidator(93)],
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "NetBox Configuration"
        verbose_name_plural = "NetBox Configurations"

    def __str__(self):
        return self.env_name

    @property
    def env_name(self):
        return os.environ.get("ENV_NAME")

    def get_absolute_url(self):
        return reverse("plugins:netbox_paas:netboxconfiguration", args=[self.pk])

    def clean(self):
        if self.__class__.objects.exists() and not self.pk:
            raise ValidationError("There can only be one NetBoxConfiguration instance.")

        # Clear any cached values from lru_cache
        self.paas.cache_clear()

        # Environment name must not contain dots
        if "." in self.env_name:
            raise ValidationError("Environment name must not contain dots.")

        if self.pk:
            try:
                # Ensure the provided env_name exists
                self.paas(self.env_name)
            except JelasticApiError as e:
                raise ValidationError(e)

        if self.env_name_storage:
            try:
                # Ensure the provided env_name exists
                self.paas(self.env_name_storage)
            except JelasticApiError as e:
                raise ValidationError(e)

        if self.license:
            if not self.license.startswith("ghp_") and not self.license.startswith("github_pat_"):
                raise ValidationError({"license": "Invalid license key"})

    @lru_cache(maxsize=2)
    def paas(self, env_name, auto_init=True):
        return PaaSNetBox(
            token=self.key,
            env_name=env_name,
            auto_init=auto_init,
        )

    def get_env(self):
        return self.paas(self.env_name)

    def get_docker_tag(self):
        return self.get_env().get_master_node(NODE_GROUP_CP).get("customitem", {}).get("dockerTag", "")

    def get_env_storage(self):
        return self.paas(self.env_name_storage)

    def netbox_admin(self):
        """
        Returns NetBox administration configuration.
        """
        paas = self.get_env()

        result = {"url": paas.get_url()}
        for setting in NETBOX_SUPERUSER_SETTINGS:
            result[setting] = paas.get_env_var(setting)

        return result

    def netbox_settings(self):
        """
        Returns NetBox settings.
        """
        config = {}
        env = self.get_env()

        # Iterate through each section in NETBOX_SETTINGS
        for section in NETBOX_SETTINGS.sections:
            section_name = section.name
            config[section_name] = []

            # Iterate through each setting in the section
            for param in section.params:
                initial = env.get_env_var(param.key, param.initial)

                # Alter list of strings to comma-separated string
                if isinstance(initial, (tuple, list)) and all([isinstance(x, str) for x in initial]):
                    initial = ", ".join(initial)

                param.initial = initial

                config[section_name].append(param)

        return config

    def apply_settings(self, data: dict):
        """
        Apply NetBox settings.
        """
        logger.debug(f"Applying NetBox settings: {data}")

        all_keys = [param.key for section in NETBOX_SETTINGS.sections for param in section.params]

        env = self.get_env()
        # Get all NetBox node groups
        node_groups = env.get_nb_node_groups()

        for node_group in node_groups:
            logger.debug(f"Applying settings to node group: {node_group}")

            node_group_name = node_group.get("name")
            env_vars = env.get_env_vars(node_group_name)

            # Filter env_vars with keys that exist in all_keys only
            env_vars = {k: v for k, v in env_vars.items() if k in all_keys}

            # Remove all filtered env_vars
            env.remove_env_vars(node_group_name, list(env_vars.keys()))

            for section, params in data.items():
                if section is None:
                    vars = {}
                    # These values are to be updated in the environment variables
                    for key, value in params.items():
                        if value:
                            vars[key] = value
                    env.add_env_vars(node_group_name, vars)

        # Update the files on the NODE_GROUP_CP with named sections
        file_content = ""
        for section, params in data.items():
            if section is not None:
                # Construct the file content
                for key, value in params.items():
                    if value:
                        try:
                            file_content += f"{key} = {ast.literal_eval(value)}\n"
                        except (ValueError, SyntaxError):
                            if isinstance(value, str):
                                file_content += f"{key} = '{value}'\n"
                            else:
                                file_content += f"{key} = {value}\n"

        file_path = f"/etc/netbox/config/extra.py"
        logger.debug(f"Writing file: {file_path}")
        # Create the section file
        env.client.environment.File.Write(
            env_name=self.env_name,
            path=file_path,
            body=file_content,
            node_group=NODE_GROUP_CP,
            master_only=True,
            is_append_mode=False,
        )

        # Schedule a restart of the NetBox environment
        self.schedule_restart()

    def enqueue(self, func, request, *args, **kwargs):
        return self.paas(self.env_name).enqueue(
            func,
            self,
            request,
            *args,
            **kwargs,
        )

    def schedule_restart(self):
        """
        Schedule a restart of the NetBox environment.
        """
        logger.debug(f"Scheduling restart of NetBox environment: {self.env_name}")
        env = self.get_env()
        env.restart_nodes(
            [group["name"] for group in env.get_nb_node_groups()],
            lazy=True,
        )


class NetBoxDBBackup(ChangeLoggedModel):
    netbox_env = models.ForeignKey(
        to=NetBoxConfiguration,
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
        return reverse("plugins:netbox_paas:netboxdbbackup", args=[self.pk])

    def __str__(self):
        return self.crontab

    def save(self, *args, **kwargs):
        self.netbox_env.enqueue(
            self.netbox_env.get_env().install_addon,
            None,
            app_id="db-backup",
            node_group=NODE_GROUP_SQLDB,
            addon_settings={
                "scheduleType": 3,
                "cronTime": self.cron,
                "storageName": self.netbox_env.env_name_storage,
                "backupCount": self.keep_backups,
                "dbuser": "webadmin",
                "dbpass": getattr(self, "_db_password", ""),
            },
        )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.netbox_env.enqueue(
            self.netbox_env.get_env().uninstall_addon,
            None,
            app_id="db-backup",
            node_group=NODE_GROUP_SQLDB,
            search={"nodeType": "postgresql", "app_id": "db-backup"},
        )

        super().delete(*args, **kwargs)

    def clean(self):
        super().clean()

        if self.__class__.objects.exists() and not self.pk:
            raise ValidationError("There can only be one NetBoxDBBackup instance.")

        # Ensure netbox_env has a storage env connected before proceeding
        if not self.netbox_env.env_name_storage:
            raise ValidationError(
                {"netbox_env": "Add a backup storage environment to the NetBoxConfiguration instance."}
            )

        if self.keep_backups > 30:
            raise ValidationError({"keep_backups": "The maximum number of backups to keep is 30."})

        if self.keep_backups < 1:
            raise ValidationError({"keep_backups": "The minimum number of backups to keep is 1."})

        try:
            croniter(self.crontab)
        except CroniterError as e:
            raise ValidationError({"crontab": e})

    @property
    def cron(self):
        return " ".join(croniter(self.crontab).expressions)

    @property
    def get_master_node(self):
        node_groups = self.netbox_env.get_env_storage().get_node_groups()
        master_node = None
        for node_group in node_groups:
            master_node = node_group.get("node", {})
            break

        return master_node

    def list_backups(self):
        master_node = self.get_master_node
        if not master_node:
            return []

        # Always update restic
        self.netbox_env.get_env_storage().execute_cmd(
            node_id=master_node.get("id"), command="/usr/bin/restic self-update 2>&1"
        )

        result = self.netbox_env.get_env_storage().execute_cmd(
            node_id=master_node.get("id"), command="/root/getBackupsAllEnvs.sh"
        )[0]

        if backups := json.loads(result.get("out", "")).get("backups", {}).get(self.netbox_env.env_name, []):
            # Cache backups in case next time it returns empty
            cache.set(f"netbox_db_backups_{self.pk}", backups, timeout=60 * 60)
        else:
            # Return cached backups if any
            backups = cache.get(f"netbox_db_backups_{self.pk}", [])

        return sorted(
            [self.__parse_backup_name(backup) for backup in backups],
            key=lambda x: x.get("datetime"),
            reverse=True,
        )

    def __parse_backup_name(self, backup_name):
        """
        Parse the backup name and return a dictionary with the values.
        """
        # Initial split at the first underscore
        parts = backup_name.split("_", 1)
        # Parse the date from the first part
        date = datetime.strptime(parts[0], "%Y-%m-%d").date()

        # Parse the time from the second part
        parts = parts[1].split("-", 1)
        timestamp, timezone = parts[0].split("_")
        # Parse the time from the first part
        time = datetime.fromtimestamp(int(timestamp)).time()

        # Combine the date and time
        date = datetime.combine(date, time)

        # Parse the backup type and the database version
        if match := re.search(r"(\w+)\((.+)\)", parts[1]):
            backup_type = match.group(1)
            db_version = match.group(2).split("-", 1)[1]
        else:
            backup_type, db_version = None, None

        return {
            "name": backup_name,
            "datetime": date,
            "timezone": timezone,
            "backup_type": backup_type,
            "db_version": db_version,
        }

    def backup(self, request=None):
        """
        Create a new database backup.
        """
        # Get installed addon
        addon = self.netbox_env.get_env().get_installed_addon(app_id="db-backup", node_group=NODE_GROUP_SQLDB)

        return self.netbox_env.enqueue(
            self.netbox_env.get_env().db_backup,
            request,
            app_unique_name=addon.get("uniqueName"),
        )

    def restore(self, request, backup_name):
        """
        Restore a database backup.
        """
        # Get installed addon
        addon = self.netbox_env.get_env().get_installed_addon(app_id="db-backup", node_group=NODE_GROUP_SQLDB)

        return self.netbox_env.enqueue(
            self.netbox_env.get_env().execute_action,
            request,
            app_unique_name=addon.get("uniqueName"),
            action="restore",
            params={
                "backupDir": backup_name,
                "backupedEnvName": self.netbox_env.env_name,
            },
        )
