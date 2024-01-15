from rest_framework import serializers
from netbox.api.serializers import NetBoxModelSerializer, WritableNestedSerializer

from ..models import *

__all__ = ["NetBoxConfigurationSerializer", "NetBoxDBBackupSerializer"]


class NetBoxConfigurationSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloud_pilot-api:netboxconfiguration-detail"
    )

    env_name = serializers.CharField(
        read_only=True,
    )
    is_enterprise = serializers.BooleanField(
        read_only=True,
    )
    key = serializers.CharField(
        write_only=True,
    )
    license = serializers.CharField(
        write_only=True,
    )

    class Meta:
        model = NetBoxConfiguration
        fields = (
            "id",
            "url",
            "display",
            "env_name",
            "env_name_storage",
            "is_enterprise",
            "license",
            "key",
            "description",
            "custom_fields",
            "comments",
            "created",
            "last_updated",
        )


class NestedNetBoxConfigurationSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_cloud_pilot-api:netboxconfiguration-detail"
    )

    class Meta:
        model = NetBoxConfiguration
        fields = ("id", "url", "display","env_name", "env_name_storage", "is_enterprise")


class NetBoxDBBackupSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="plugins-api:netbox_cloud_pilot-api:netboxdbbackup-detail")

    netbox_env = NestedNetBoxConfigurationSerializer()

    class Meta:
        model = NetBoxDBBackup
        fields = ("id", "url", "display", "netbox_env", "crontab", "keep_backups")
