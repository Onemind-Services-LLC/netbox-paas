from netbox.api.serializers import NetBoxModelSerializer

from ..models import *

__all__ = [
    "NetBoxConfigurationSerializer",
]


class NetBoxConfigurationSerializer(NetBoxModelSerializer):
    class Meta:
        model = NetBoxConfiguration
        fields = (
            "id",
            "key",
        )
