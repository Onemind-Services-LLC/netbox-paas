# Generated by Django 4.1.10 on 2023-12-26 21:43

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers
import utilities.json


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('extras', '0092_delete_jobresult'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetBoxConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('custom_field_data', models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
                ('description', models.CharField(blank=True, max_length=200)),
                ('comments', models.TextField(blank=True)),
                ('key', models.CharField(max_length=255, unique=True, validators=[django.core.validators.MinLengthValidator(40)])),
                ('env_name_storage', models.CharField(blank=True, max_length=255, unique=True, validators=[django.core.validators.MinLengthValidator(5)])),
                ('license', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.MinLengthValidator(40), django.core.validators.MaxLengthValidator(93)])),
                ('tags', taggit.managers.TaggableManager(through='extras.TaggedItem', to='extras.Tag')),
            ],
            options={
                'verbose_name': 'NetBox Configuration',
                'verbose_name_plural': 'NetBox Configurations',
            },
        ),
        migrations.CreateModel(
            name='NetBoxDBBackup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('crontab', models.CharField(default='@daily', max_length=255)),
                ('keep_backups', models.PositiveIntegerField(default=1)),
                ('netbox_env', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='db_backups', to='netbox_paas.netboxconfiguration')),
            ],
            options={
                'verbose_name': 'NetBox DB Backup',
                'verbose_name_plural': 'NetBox DB Backups',
            },
        ),
    ]
