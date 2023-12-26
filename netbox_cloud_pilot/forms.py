from django import forms
from django.forms import ValidationError

from netbox.forms import NetBoxModelForm
from utilities.forms import BootstrapMixin
from utilities.forms.fields import CommentField
from .constants import NETBOX_SETTINGS
from .models import *

__all__ = ("NetBoxConfigurationForm", "NetBoxSettingsForm", "NetBoxBackupStorageForm")


def create_fieldset():
    """
    Create a fieldset from a dict of settings.
    """
    fieldset = ()

    for section, settings in NETBOX_SETTINGS.items():
        fields = []
        for setting in settings:
            for key, value in setting.items():
                fields.append(key.lower())
        fieldset += ((section, fields),)

    return fieldset


class NetBoxConfigurationForm(NetBoxModelForm):
    key = forms.CharField(
        help_text="Jelastic API token where the NetBox instance is running.",
    )

    env_name = forms.CharField(
        label="Environment Name",
        help_text="Jelastic environment name where the NetBox instance is running.",
    )

    env_name_storage = forms.CharField(
        label="Environment Name",
        required=False,
        help_text="Jelastic environment name where the backup storage is running.",
    )

    comments = CommentField()

    fieldsets = (
        (None, ("key", "env_name", "description")),
        ('Backup', ("env_name_storage",)),
    )

    class Meta:
        model = NetBoxConfiguration
        fields = ("key", "env_name", "description", "env_name_storage")


class NetBoxSettingsForm(BootstrapMixin, forms.Form):
    fieldsets = create_fieldset()

    class Meta:
        fields = [
            key.lower()
            for value in NETBOX_SETTINGS.values()
            for v in value
            for key in v
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically create fields for each setting
        for _, settings in kwargs.get("initial", {}).items():
            for setting in settings:
                for key, value in setting.items():
                    field_type = value.pop("field_type", "TextInput")
                    placeholder = value.pop("placeholder", None)

                    self.fields[key.lower()] = forms.CharField(
                        **value,
                        widget=getattr(forms, field_type)(
                            attrs={"placeholder": placeholder, "class": "form-control"}
                        ),
                    )


class NetBoxBackupStorageForm(BootstrapMixin, forms.Form):
    deployment = forms.ChoiceField(
        choices=(
            ("standalone", "Standalone"),
            ("cluster", "Cluster"),
        )
    )

    node_count = forms.ChoiceField(
        choices=(
            (1, 1),
            (3, 3),
            (5, 5),
            (7, 7)
        ),
        initial=1,
        help_text="Number of nodes in the cluster.",
        required=False
    )

    storage_size = forms.IntegerField(
        label="Storage Size",
        required=False,
        help_text="Size of the storage in GB.",
        initial=10,
        max_value=200
    )

    region = forms.ChoiceField(
        help_text="Region where the storage will be deployed, this can be different from the NetBox instance region."
    )

    display_name = forms.CharField(
        label="Display Name",
        help_text="Display name for the storage.",
        max_length=50,
        initial="Backup Storage"
    )

    fieldsets = (
        (None, ("display_name", "storage_size", "region")),
        ("Deployment", ("deployment", "node_count"))
    )

    class Meta:
        fields = [
            "deployment",
            "node_count",
            "storage_size",
            "region",
            "display_name",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fetch the region list and build the choices
        nc = NetBoxConfiguration.objects.first()
        regions = nc._jelastic().environment.Control.GetRegions().get('array', [])
        self.fields['region'].choices = [(hard_node_group['uniqueName'], region['displayName']) for region in regions for hard_node_group in region['hardNodeGroups']]

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["deployment"] == "cluster":
            if cleaned_data["node_count"] == '1':
                raise ValidationError({
                    "node_count": "Node count must be greater than 1 for a cluster deployment."
                })

        if cleaned_data["deployment"] == "standalone":
            if cleaned_data["node_count"] != '1':
                raise ValidationError({
                    "node_count": "Node count must be 1 for a standalone deployment."
                })

        return cleaned_data
