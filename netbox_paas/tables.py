import django_tables2 as tables
from netbox.tables import columns


__all__ = ("NetBoxBackupsTable",)

RESTORE_BUTTON = """
<form method="post" action="{% url 'plugins:netbox_paas:netboxdbbackup_restore' pk=object.pk %}">
  {% csrf_token %}
  <input type="hidden" name="name" value="{{ record.name }}">
  <button type="submit" class="btn btn-sm btn-warning">
    <i class="mdi mdi-restore"></i> Restore
  </button>
</form>
"""


class NetBoxBackupsTable(tables.Table):
    name = tables.Column(
        orderable=False,
    )
    datetime = columns.DateTimeColumn(
        orderable=False,
        verbose_name="Date/Time",
    )
    timezone = tables.Column(
        orderable=False,
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

    actions = columns.TemplateColumn(
        template_code=RESTORE_BUTTON,
        orderable=False,
        verbose_name="Actions",
    )

    class Meta:
        fields = ("name", "datetime", "timezone", "backup_type", "db_version", "actions")
        attrs = {
            "class": "table table-hover object-list",
        }
