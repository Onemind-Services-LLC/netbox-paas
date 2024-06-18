from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from django.conf import settings
from importlib.metadata import metadata
from rest_framework import serializers
from netbox.api.serializers import NetBoxModelSerializer, WritableNestedSerializer

from ..models import *
from ..utils import is_upgrade_available, filter_releases

__all__ = [
    "NetBoxConfigurationSerializer",
    "NetBoxDBBackupSerializer",
    "NestedNetBoxConfigurationSerializer",
    "NetBoxPluginSerializer",
    "NetBoxPluginInstallSerializer",
]


class NetBoxConfigurationSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_paas-api:netboxconfiguration-detail")

    env_name = serializers.CharField(
        read_only=True,
    )
    key = serializers.CharField(
        write_only=True,
    )
    license = serializers.CharField(write_only=True, allow_blank=True)

    class Meta:
        model = NetBoxConfiguration
        fields = (
            "id",
            "url",
            "display",
            "env_name",
            "env_name_storage",
            "license",
            "key",
            "description",
            "custom_fields",
            "comments",
            "created",
            "last_updated",
        )


class NestedNetBoxConfigurationSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_paas-api:netboxconfiguration-detail")

    class Meta:
        model = NetBoxConfiguration
        fields = ("id", "url", "display", "env_name", "env_name_storage")


class NetBoxDBBackupSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_paas-api:netboxdbbackup-detail")

    netbox_env = NestedNetBoxConfigurationSerializer()

    class Meta:
        model = NetBoxDBBackup
        fields = ("id", "url", "display", "netbox_env", "crontab", "keep_backups")


class NetBoxPluginOwnerSerializer(serializers.Serializer):
    name = serializers.CharField()
    url = serializers.URLField()

    class Meta:
        fields = (
            "name",
            "url",
        )


class NetBoxPluginSerializer(serializers.Serializer):
    plugin_id = serializers.CharField()
    name = serializers.CharField()
    display = serializers.SerializerMethodField(read_only=True)
    app_label = serializers.CharField()
    description = serializers.CharField()
    github_api_url = serializers.URLField()
    github_url = serializers.URLField()
    owner = NetBoxPluginOwnerSerializer()
    private = serializers.BooleanField()
    pypi_url = serializers.URLField(
        required=False,
    )
    releases = serializers.SerializerMethodField(
        required=False,
    )
    is_installed = serializers.SerializerMethodField(
        read_only=True,
    )
    current_version = serializers.SerializerMethodField(
        read_only=True,
    )
    upgrade_available = serializers.SerializerMethodField(
        read_only=True,
    )

    @extend_schema_field(OpenApiTypes.STR)
    def get_display(self, obj):
        return obj["name"]

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_installed(self, obj):
        return obj["app_label"] in settings.PLUGINS

    @extend_schema_field(OpenApiTypes.STR)
    def get_current_version(self, obj):
        if not self.get_is_installed(obj):
            return None

        return metadata(obj["app_label"]).get("Version", None)

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_upgrade_available(self, obj):
        if not self.get_is_installed(obj):
            return False

        plugin = self.context['plugins'][obj["plugin_id"]]
        return is_upgrade_available(plugin, self.get_current_version(obj))

    def get_releases(self, obj):
        plugin = self.context['plugins'][obj["plugin_id"]]
        return filter_releases(plugin)


class NetBoxPluginInstallSerializer(serializers.Serializer):
    plugin_id = serializers.CharField()
    version = serializers.CharField()
    configuration = serializers.JSONField(
        required=False,
    )

    class Meta:
        fields = (
            "plugin_id",
            "version",
            "configuration",
        )

    def validate_plugin_id(self, value):
        if value not in self.context['plugins']:
            raise serializers.ValidationError(f"Plugin '{value}' not found.")

        return value
