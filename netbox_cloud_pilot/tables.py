import django_tables2 as tables
from netbox.tables import columns


__all__ = (
    "NetBoxBackupsTable",
)


class NetBoxBackupsTable(tables.Table):
    name = tables.Column(
        orderable=False,
    )
    datetime = columns.DateTimeColumn(
        orderable=False,
        verbose_name="Date/Time",
    )

    backup_type = columns.TemplateColumn(
        template_code="""{{ record.backup_type|title }}""",
        orderable=False,
        verbose_name="Backup Type",
    )

    db_version = tables.Column(
        orderable=False,
        verbose_name="Database Version",
    )

    class Meta:
        fields = ("name", "datetime", "backup_type", "db_version")
        attrs = {
            'class': 'table table-hover object-list',
        }
