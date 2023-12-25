from django import forms

from netbox.forms import NetBoxModelForm
from utilities.forms import BootstrapMixin
from utilities.forms.fields import CommentField
from .constants import NETBOX_SETTINGS
from .models import *

__all__ = ("NetBoxConfigurationForm", "NetBoxSettingsForm")


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

    comments = CommentField()

    class Meta:
        model = NetBoxConfiguration
        fields = ("key", "env_name", "description")


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
