from django import forms

from netbox.forms import NetBoxModelForm
from utilities.forms.fields import CommentField
from .models import *

__all__ = ("NetBoxConfigurationForm",)


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
