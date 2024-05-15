# Generated by Django 4.2.8 on 2024-05-10 05:43

from django.db import migrations, models
import django.db.models.deletion


def named_tuple_fetch_all(cursor):
    "Return all rows from a cursor as a namedtuple"
    from collections import namedtuple

    desc = cursor.description
    Result = namedtuple("Result", [col[0] for col in desc])
    return [Result(*row) for row in cursor.fetchall()]


def rename_indexes(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT indexname FROM pg_indexes WHERE tablename LIKE 'netbox_cloud_pilot%'")
        for result in named_tuple_fetch_all(cursor):
            old_index_name = result.indexname
            new_index_name = old_index_name.replace("netbox_cloud_pilot_", "netbox_paas_", 1)
            cursor.execute(f"ALTER INDEX IF EXISTS {old_index_name} RENAME TO {new_index_name}")


def rename_foreignkeys(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name, constraint_name
            FROM information_schema.key_column_usage
            WHERE constraint_catalog=CURRENT_CATALOG
            AND table_name LIKE 'netbox_cloud_pilot%'
            AND position_in_unique_constraint notnull
            """
        )
        for result in named_tuple_fetch_all(cursor):
            table_name = result.table_name
            old_foreignkey_name = result.constraint_name
            new_foreignkey_name = old_foreignkey_name.replace("netbox_cloud_pilot_", "netbox_paas_", 1)
            cursor.execute(f"ALTER TABLE {table_name} RENAME CONSTRAINT {old_foreignkey_name} TO {new_foreignkey_name}")


def migrate_models(apps, schema_editor):
    OldModel1 = apps.get_model('netbox_cloud_pilot', 'NetBoxConfiguration')
    NewModel1 = apps.get_model('netbox_paas', 'NetBoxConfiguration')

    OldModel2 = apps.get_model('netbox_cloud_pilot', 'NetBoxDBBackup')
    NewModel2 = apps.get_model('netbox_paas', 'NetBoxDBBackup')

    # Check if the table with the old app name exists for both models
    if (
        schema_editor.connection.introspection.table_name_converter(OldModel1._meta.db_table)
        in schema_editor.connection.introspection.table_names()
    ):
        # Rename the table with the old app name to the new app name for Model 1
        schema_editor.execute(
            "ALTER TABLE {} RENAME TO {}".format(
                schema_editor.quote_name(OldModel1._meta.db_table),
                schema_editor.quote_name(NewModel1._meta.db_table),
            )
        )

    if (
        schema_editor.connection.introspection.table_name_converter(OldModel2._meta.db_table)
        in schema_editor.connection.introspection.table_names()
    ):
        # Rename the table with the old app name to the new app name for Model 2
        schema_editor.execute(
            "ALTER TABLE {} RENAME TO {}".format(
                schema_editor.quote_name(OldModel2._meta.db_table),
                schema_editor.quote_name(NewModel2._meta.db_table),
            )
        )


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_paas', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='netboxdbbackup',
            name='netbox_env',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='db_backups',
                to='netbox_paas.netboxconfiguration',
            ),
        ),
        migrations.RunPython(rename_indexes, migrations.RunPython.noop),
        migrations.RunPython(rename_foreignkeys, migrations.RunPython.noop),
        migrations.RunPython(migrate_models),
    ]
