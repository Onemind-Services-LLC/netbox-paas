import random
import string

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.generic import View
from jelastic.api.exceptions import JelasticApiError

from netbox.views import generic
from utilities.views import register_model_view, GetReturnURLMixin
from . import forms, models, tables


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
        env_name = request.POST.get("env_name")
        node_id = request.POST.get("node_id")

        node = instance.env_node(env_name, node_id)
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


@register_model_view(models.NetBoxConfiguration, "restart")
class NetBoxRestartView(PermissionRequiredMixin, View):
    def get_permission_required(self):
        return ["netbox_cloud_pilot.change_netboxconfiguration"]

    def post(self, request, pk):
        """
        Restarts container by node group.
        """
        instance = get_object_or_404(models.NetBoxConfiguration, pk=pk)
        node_group = request.POST.get("node_group")
        instance.restart_node_group(node_group)
        messages.success(request, "Restarted successfully.")
        return redirect(
            "plugins:netbox_cloud_pilot:netboxconfiguration", pk=instance.pk
        )


@register_model_view(
    models.NetBoxConfiguration, "backup_storage", path="backup-storage"
)
class NetBoxStorageView(PermissionRequiredMixin, GetReturnURLMixin, View):
    def get_permission_required(self):
        return ["netbox_cloud_pilot.view_netboxconfiguration"]

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(models.NetBoxConfiguration, pk=kwargs["pk"])
        form = forms.NetBoxBackupStorageForm()

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

        form = forms.NetBoxBackupStorageForm(request.POST)
        if form.is_valid():
            # Generate a random env name
            env_name = "env-"
            env_name += "".join([random.choice(string.digits) for _ in range(7)])

            # Deploy a new environment for backup-storage
            jc = obj._jelastic()
            jc.marketplace.App.Install(
                id="wp-restore",
                env_name=env_name,
                settings={
                    "customName": form.cleaned_data["deployment"],
                    "storageNodesCount": form.cleaned_data["node_count"],
                    "diskspace": form.cleaned_data["storage_size"],
                },
                display_name=form.cleaned_data["display_name"],
                region=form.cleaned_data["region"],
                skip_email=True,
            )
            obj.env_name_storage = env_name
            obj.save()

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


@register_model_view(models.NetBoxDBBackup)
class NetBoxDBBackupView(generic.ObjectView):
    queryset = models.NetBoxDBBackup.objects.all()

    def get_extra_context(self, request, instance):
        table = tables.NetBoxBackupsTable(instance.list_backups())

        return {
            "backup_table": table
        }


class NetBoxDBBackupListView(generic.ObjectListView):
    queryset = models.NetBoxDBBackup.objects.all()

    def get(self, request):
        if obj := models.NetBoxDBBackup.objects.first():
            return redirect("plugins:netbox_cloud_pilot:netboxdbbackup", pk=obj.pk)

        return redirect("plugins:netbox_cloud_pilot:netboxdbbackup_add")


@register_model_view(models.NetBoxDBBackup, "edit")
class NetBoxDBBackupEditView(generic.ObjectEditView):
    queryset = models.NetBoxDBBackup.objects.all()
    form = forms.NetBoxDBBackupForm


@register_model_view(models.NetBoxDBBackup, "delete")
class NetBoxDBBackupDeleteView(generic.ObjectDeleteView):
    queryset = models.NetBoxDBBackup.objects.all()


@register_model_view(models.NetBoxDBBackup, "backup")
class NetBoxDBBackupBackupView(PermissionRequiredMixin, View):
    def get_permission_required(self):
        return ["netbox_cloud_pilot.change_netboxdbbackup"]

    def post(self, request, pk):
        """
        Create a new backup.
        """
        instance = get_object_or_404(models.NetBoxDBBackup, pk=pk)

        try:
            instance.backup()
            messages.success(request, "Backup created successfully.")
        except JelasticApiError as e:
            messages.error(request, e)

        return redirect(
            "plugins:netbox_cloud_pilot:netboxdbbackup", pk=instance.pk
        )
