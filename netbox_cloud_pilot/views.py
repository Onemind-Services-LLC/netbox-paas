from netbox.views import generic
from utilities.views import register_model_view
from . import forms, models, tables


@register_model_view(models.NetBoxConfiguration)
class NetBoxConfigurationView(generic.ObjectView):
    queryset = models.NetBoxConfiguration.objects.all()


class NetBoxConfigurationListView(generic.ObjectListView):
    queryset = models.NetBoxConfiguration.objects.all()
    table = tables.NetBoxConfigurationTable


@register_model_view(models.NetBoxConfiguration, "edit")
class NetBoxConfigurationEditView(generic.ObjectEditView):
    queryset = models.NetBoxConfiguration.objects.all()
    form = forms.NetBoxConfigurationForm


@register_model_view(models.NetBoxConfiguration, "delete")
class NetBoxConfigurationDeleteView(generic.ObjectDeleteView):
    queryset = models.NetBoxConfiguration.objects.all()
