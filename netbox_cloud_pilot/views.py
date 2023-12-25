from django.shortcuts import redirect

from netbox.views import generic
from utilities.views import register_model_view
from . import forms, models


@register_model_view(models.NetBoxConfiguration)
class NetBoxConfigurationView(generic.ObjectView):
    queryset = models.NetBoxConfiguration.objects.all()


class NetBoxConfigurationListView(generic.ObjectListView):
    queryset = models.NetBoxConfiguration.objects.all()

    def get(self, request):
        if obj := models.NetBoxConfiguration.objects.first():
            return redirect("plugins:netbox_cloud_pilot:netboxconfiguration", pk=obj.pk)

        return redirect("plugins:netbox_cloud_pilot:netboxconfiguration_add")


@register_model_view(models.NetBoxConfiguration, "edit")
class NetBoxConfigurationEditView(generic.ObjectEditView):
    queryset = models.NetBoxConfiguration.objects.all()
    form = forms.NetBoxConfigurationForm


@register_model_view(models.NetBoxConfiguration, "delete")
class NetBoxConfigurationDeleteView(generic.ObjectDeleteView):
    queryset = models.NetBoxConfiguration.objects.all()
