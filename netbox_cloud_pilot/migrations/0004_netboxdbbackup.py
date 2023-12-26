# Generated by Django 4.1.10 on 2023-12-26 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_cloud_pilot', '0003_netboxconfiguration_env_name_storage_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetBoxDBBackup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('crontab', models.CharField(max_length=255)),
                ('keep_backups', models.PositiveIntegerField(default=1)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
