from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.generic import View

from netbox.views import generic
from utilities.views import register_model_view, GetReturnURLMixin
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


@register_model_view(models.NetBoxConfiguration, "logs")
class NetBoxNodeLog(PermissionRequiredMixin, View):
    def get_permission_required(self):
        return ["netbox_cloud_pilot.view_netboxconfiguration"]

    def post(self, request, pk):
        """
        Retrieve logs from Jelastic and return them as a response.
        """
        instance = get_object_or_404(models.NetBoxConfiguration, pk=pk)
        node_id = request.POST.get("node_id")

        node = instance.env_node(node_id)
        logs = instance.read_node_log(node_id)
        return render(
            request,
            "netbox_cloud_pilot/nodelogs.html",
            {
                "object": instance,
                "node": node,
                "logs": logs,
            },
        )


@register_model_view(models.NetBoxConfiguration, "settings")
class NetBoxSettingsView(PermissionRequiredMixin, GetReturnURLMixin, View):
    def get_permission_required(self):
        return ["netbox_cloud_pilot.change_netboxconfiguration"]

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(models.NetBoxConfiguration, pk=kwargs["pk"])
        form = forms.NetBoxSettingsForm(initial=obj.netbox_settings)

        return render(
            request,
            "generic/object_edit.html",
            {
                "model": models.NetBoxConfiguration,
                "object": obj,
                "form": form,
                "return_url": reverse(
                    "plugins:netbox_cloud_pilot:netboxconfiguration",
                    kwargs={"pk": obj.pk},
                ),
            },
        )

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(models.NetBoxConfiguration, pk=kwargs["pk"])

        form = forms.NetBoxSettingsForm(request.POST, initial=obj.netbox_settings)
        if form.is_valid():
            # All keys must be uppercase
            form_data = {k.upper(): v for k, v in form.cleaned_data.items()}
            # Call Jelastic to apply the ENV_VARs on all NetBox nodes (including workers)
            obj.apply_settings(form_data)
            messages.success(request, "Settings applied successfully.")
            return_url = self.get_return_url(request, obj)
            return redirect(return_url)

        return render(
            request,
            "generic/object_edit.html",
            {
                "object": obj,
                "form": form,
                "return_url": self.get_return_url(request, obj),
            },
        )
