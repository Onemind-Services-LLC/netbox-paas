import django_tables2 as tables
from netbox.tables import NetBoxTable, columns
from .models import NetBoxConfiguration

__all__ = ("NetBoxConfigurationTable",)


class NetBoxConfigurationTable(NetBoxTable):
    env_name = tables.Column(linkify=True)

    tags = columns.TagColumn(
        url_name="plugins:netbox_cloud_pilot:netboxconfiguration_list"
    )

    class Meta(NetBoxTable.Meta):
        model = NetBoxConfiguration
        fields = (
            "pk",
            "id",
            "env_name",
            "description",
            "comments",
            "tags",
            "created",
            "last_updated",
        )
        default_columns = (
            "id",
            "env_name",
            "description",
        )
