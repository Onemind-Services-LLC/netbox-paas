from django import forms
from django.conf import settings
from django.forms import ValidationError

from netbox.forms import NetBoxModelForm
from utilities.forms import BootstrapMixin
from utilities.forms.fields import CommentField
from .constants import NETBOX_SETTINGS
from .models import *
from .utils import *

__all__ = (
    "NetBoxConfigurationForm",
    "NetBoxSettingsForm",
    "NetBoxBackupStorageForm",
    "NetBoxDBBackupForm",
    "NetBoxPluginInstallForm",
)


def create_fieldset():
    """
    Create a fieldset from a dict of settings.
    """
    fieldset = ()

    for section, settings in NETBOX_SETTINGS.items():
        fields = []
        for setting in settings:
            for key, value in setting.items():
                fields.append(key.lower())
        fieldset += ((section, fields),)

    return fieldset


class NetBoxConfigurationForm(NetBoxModelForm):
    key = forms.CharField(
        help_text="Jelastic API token where the NetBox instance is running.",
    )

    env_name = forms.CharField(
        label="Environment Name",
        help_text="Jelastic environment name where the NetBox instance is running.",
    )

    env_name_storage = forms.CharField(
        label="Environment Name",
        required=False,
        help_text="Jelastic environment name where the backup storage is running.",
    )

    license = forms.CharField(
        required=False,
        help_text="NetBox Enterprise license key.",
    )

    comments = CommentField()

    fieldsets = (
        (None, ("key", "env_name", "description")),
        ("Backup", ("env_name_storage",)),
        ("Enterprise", ("license",)),
    )

    class Meta:
        model = NetBoxConfiguration
        fields = ("key", "env_name", "description", "env_name_storage", "license",)


class NetBoxSettingsForm(BootstrapMixin, forms.Form):
    fieldsets = create_fieldset()

    class Meta:
        fields = [
            key.lower()
            for value in NETBOX_SETTINGS.values()
            for v in value
            for key in v
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically create fields for each setting
        for _, settings in kwargs.get("initial", {}).items():
            for setting in settings:
                for key, value in setting.items():
                    field_type = value.pop("field_type", "TextInput")
                    placeholder = value.pop("placeholder", None)

                    self.fields[key.lower()] = forms.CharField(
                        **value,
                        widget=getattr(forms, field_type)(
                            attrs={"placeholder": placeholder, "class": "form-control"}
                        ),
                    )


class NetBoxBackupStorageForm(BootstrapMixin, forms.Form):
    deployment = forms.ChoiceField(
        choices=(
            ("standalone", "Standalone"),
            ("cluster", "Cluster"),
        )
    )

    node_count = forms.ChoiceField(
        choices=((1, 1), (3, 3), (5, 5), (7, 7)),
        initial=1,
        help_text="Number of nodes in the cluster.",
        required=False,
    )

    storage_size = forms.IntegerField(
        label="Storage Size",
        required=False,
        help_text="Size of the storage in GB.",
        initial=10,
        max_value=200,
    )

    region = forms.ChoiceField(
        help_text="Region where the storage will be deployed, this can be different from the NetBox instance region."
    )

    display_name = forms.CharField(
        label="Display Name",
        help_text="Display name for the storage.",
        max_length=50,
        initial="Backup Storage",
    )

    fieldsets = (
        (None, ("display_name", "storage_size", "region")),
        ("Deployment", ("deployment", "node_count")),
    )

    class Meta:
        fields = [
            "deployment",
            "node_count",
            "storage_size",
            "region",
            "display_name",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fetch the region list and build the choices
        nc = NetBoxConfiguration.objects.first()
        regions = nc._jelastic().environment.Control.GetRegions().get("array", [])
        self.fields["region"].choices = [
            (hard_node_group["uniqueName"], region["displayName"])
            for region in regions
            for hard_node_group in region["hardNodeGroups"]
        ]

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["deployment"] == "cluster":
            if cleaned_data["node_count"] == "1":
                raise ValidationError(
                    {
                        "node_count": "Node count must be greater than 1 for a cluster deployment."
                    }
                )

        if cleaned_data["deployment"] == "standalone":
            if cleaned_data["node_count"] != "1":
                raise ValidationError(
                    {"node_count": "Node count must be 1 for a standalone deployment."}
                )

        return cleaned_data


class NetBoxDBBackupForm(NetBoxModelForm):
    db_password = forms.CharField(
        label="Database Password",
        help_text="Password for the <strong>webadmin</strong> user. You will find this in your email.",
        required=False,
    )

    tags = None

    fieldsets = (
        (None, ("netbox_env", "db_password")),
        ("Backup", ("crontab", "keep_backups")),
    )

    class Meta:
        model = NetBoxDBBackup
        fields = ["netbox_env", "crontab", "keep_backups", "db_password"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            # Fetch the database password from the addon settings
            app = self.instance.get_installed_app("db-backup")
            settings = app.get("settings", {}).get("main", {}).get("data", {})
            self.fields["db_password"].initial = settings.get("dbpass")

    def clean(self):
        super().clean()

        if db_password := self.cleaned_data.get("db_password"):
            self.instance._db_password = db_password

        if not self.instance.pk and not db_password:
            raise ValidationError(
                {"db_password": "This field is required when adding a new backup."}
            )


class NetBoxPluginInstallForm(BootstrapMixin, forms.Form):
    plugin_name = forms.CharField(
        label="Plugin Name",
        help_text="Name of the plugin to install.",
        max_length=255,
        disabled=True,
    )

    plugin_version = forms.ChoiceField(
        label="Plugin Version",
        help_text="Version of the plugin to install.",
    )

    configuration = forms.JSONField(
        label="Configuration",
        help_text="Configuration for the plugin.",
        required=False,
        initial={}
    )

    fieldsets = (
        (None, ("plugin_name", "plugin_version")),
        ("Configuration", ("configuration",)),
    )

    class Meta:
        fields = ["plugin_name", "plugin_version", "configuration"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        initial = kwargs.get("initial", {})

        # Get the plugins.yaml
        plugins = get_plugins_list()
        plugin = plugins.get(initial.get("plugin_name"))
        self.fields["plugin_version"].choices = [
            (release, release) for release in filter_releases(plugin)
        ]

        if initial.get('type') == 'update':
            from django.apps import apps
            plugin_name = plugin.get('netbox_name')
            app = apps.get_app_config(plugin_name)
            self.fields['plugin_version'].initial = app.version
            self.fields['configuration'].initial = settings.PLUGINS_CONFIG[plugin_name]

    def clean(self):
        plugins = get_plugins_list()
        plugin = plugins.get(self.cleaned_data.get("plugin_name"))

        # Get the required_settings from the plugin
        required_settings = plugin.get("required_settings", [])
        configuration = self.cleaned_data.get("configuration")

        # Check if the required_settings are in the configuration
        if not all(key in configuration.keys() for key in required_settings):
            raise ValidationError(
                {
                    "configuration": f"Missing required settings: {', '.join(required_settings)}"
                }
            )
