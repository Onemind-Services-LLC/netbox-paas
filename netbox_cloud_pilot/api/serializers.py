from netbox.api.serializers import NetBoxModelSerializer

from ..models import *

__all__ = ["NetBoxConfigurationSerializer", "NetBoxDBBackupSerializer"]


class NetBoxConfigurationSerializer(NetBoxModelSerializer):
    class Meta:
        model = NetBoxConfiguration
        fields = (
            "id",
            "key",
        )


class NetBoxDBBackupSerializer(NetBoxModelSerializer):
    class Meta:
        model = NetBoxDBBackup
        fields = ("id", "crontab", "keep_backups")
