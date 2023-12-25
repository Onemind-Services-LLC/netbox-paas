from django import forms

from netbox.forms import NetBoxModelForm
from utilities.forms import BootstrapMixin
from utilities.forms.fields import CommentField
from .constants import NETBOX_SETTINGS
from .models import *

__all__ = ("NetBoxConfigurationForm", "NetBoxSettingsForm")


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
    fieldsets = tuple(
        (key.capitalize(), tuple(v.lower() for v in value))
        for key, value in NETBOX_SETTINGS.items()
    )

    class Meta:
        fields = [
            item.lower() for sublist in NETBOX_SETTINGS.values() for item in sublist
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically create fields for each setting
        for key, value in NETBOX_SETTINGS.items():
            for setting in value:
                self.fields[setting.lower()] = forms.CharField(
                    label=setting,
                    required=False,
                    widget=forms.TextInput(attrs={"class": "form-control"}),
                    initial=kwargs.get("initial", {}).get(key, {}).get(setting, None),
                )
