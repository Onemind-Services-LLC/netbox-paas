import random
import string

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.generic import View
from jelastic.api.exceptions import JelasticApiError

from netbox.views import generic
from utilities.forms import ConfirmationForm
from utilities.utils import normalize_querydict
from utilities.views import register_model_view, GetReturnURLMixin
from . import constants, forms, models, tables, utils


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

        iaas = instance.iaas(env_name)

        node = iaas.get_node(node_id)
        logs = iaas.get_node_log(node_id)
        return render(
            request,
            "netbox_cloud_pilot/nodelogs.html",
            {
                "object": instance,
                "env_name": env_name,
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
        form = forms.NetBoxSettingsForm(initial=obj.netbox_settings())

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

        form = forms.NetBoxSettingsForm(request.POST, initial=obj.netbox_settings())
        if form.is_valid():
            # All keys must be uppercase
            form_data = {k.upper(): v for k, v in form.cleaned_data.items()}
            # Call Jelastic to apply the ENV_VARs on all NetBox nodes (including workers)
            job = obj.enqueue_job(obj.apply_settings, data=form_data, request=request)
            messages.success(
                request,
                "Job has been created successfully.",
            )
            return redirect("core:job", pk=job.pk)

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
        env_name = request.POST.get("env_name")
        node_group = request.POST.get("node_group")
        job = instance.enqueue(
            instance.iaas(env_name, auto_init=False).restart_nodes,
            request,
            node_groups=[node_group],
        )
        messages.success(request, utils.job_msg(job))
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
            job = obj.enqueue(
                obj.iaas(env_name, auto_init=False).client.marketplace.App.Install,
                request,
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

            messages.success(request, utils.job_msg(job))
            return redirect("core:job", pk=job.pk)

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

        return {"backup_table": table}


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

        job = instance.backup(request)
        messages.success(request, utils.job_msg(job))
        return redirect("core:job", pk=job.pk)


@register_model_view(models.NetBoxDBBackup, "restore")
class NetBoxDBBackupRestoreView(PermissionRequiredMixin, View):
    def get_permission_required(self):
        return ["netbox_cloud_pilot.change_netboxdbbackup"]

    def post(self, request, pk):
        """
        Restore a backup.
        """
        instance = get_object_or_404(models.NetBoxDBBackup, pk=pk)
        backup_name = request.POST.get("name")

        job = instance.restore(request, backup_name)
        messages.success(request, utils.job_msg(job))
        return redirect("plugins:netbox_cloud_pilot:netboxdbbackup", pk=instance.pk)


class NetBoxPluginListView(View):
    def get(self, request):
        if nc := models.NetBoxConfiguration.objects.first():
            addons = nc.get_env().get_addons(
                node_group=constants.NODE_GROUP_CP,
                search={"categories": ["apps/netbox-plugins"]},
            )

            plugins = utils.get_plugins_list()

            # Find which addon is installed and update the plugins list
            for addon in addons:
                for plugin_name in plugins:
                    if addon["app_id"] == plugin_name:
                        plugins[plugin_name].update(
                            {
                                "installed": addon["isInstalled"],
                            }
                        )

            return render(
                request,
                "netbox_cloud_pilot/plugins_store.html",
                {"object": nc, "plugins": plugins},
            )

        messages.error(request, "You must configure NetBox first.")
        return redirect("plugins:netbox_cloud_pilot:netboxconfiguration_add")


@register_model_view(
    models.NetBoxConfiguration, "plugin_install", path="plugin-install"
)
class NetBoxPluginInstallView(generic.ObjectEditView):
    queryset = models.NetBoxConfiguration.objects.all()
    form = forms.NetBoxPluginInstallForm

    def initialize_form(self, request):
        data = request.POST if request.method == "POST" else None
        initial_data = normalize_querydict(request.GET)

        form = self.form(data=data, initial=initial_data)

        return form

    def get(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        obj = self.alter_object(obj, request, args, kwargs)
        model = self.queryset.model

        form = self.initialize_form(request)
        return render(
            request,
            self.template_name,
            {
                "model": model,
                "object": obj,
                "form": form,
                "return_url": self.get_return_url(request, obj),
                **self.get_extra_context(request, obj),
            },
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        form = self.initialize_form(request)

        if form.is_valid():
            plugin = utils.get_plugins_list().get(form.cleaned_data["plugin_name"])

            job = obj.enqueue(
                obj.get_env().install_plugin,
                request,
                app_id=form.cleaned_data["plugin_name"],
                version=form.cleaned_data["plugin_version"],
                netbox_name=plugin["netbox_name"],
                plugin_settings=form.cleaned_data["configuration"],
            )
            messages.success(request, utils.job_msg(job))
            return redirect("core:job", pk=job.pk)

        return render(
            request,
            self.template_name,
            {
                "object": obj,
                "form": form,
                "return_url": self.get_return_url(request, obj),
                **self.get_extra_context(request, obj),
            },
        )


@register_model_view(
    models.NetBoxConfiguration, "plugin_uninstall", path="plugin-uninstall"
)
class NetBoxPluginUninstallView(generic.ObjectDeleteView):
    queryset = models.NetBoxConfiguration.objects.all()
    template_name = "netbox_cloud_pilot/plugin_uninstall.html"

    def get(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        plugin = utils.get_plugins_list().get(request.GET.get("plugin_name"))

        if plugin is None:
            messages.error(request, "Plugin not found.")
            return redirect("plugins:netbox_cloud_pilot:netboxplugin_list")

        form = ConfirmationForm(initial=request.GET)

        return render(
            request,
            self.template_name,
            {
                "object": obj,
                "plugin": plugin,
                "form": form,
                "return_url": self.get_return_url(request, obj),
                **self.get_extra_context(request, obj),
            },
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        form = ConfirmationForm(request.POST)

        plugin = utils.get_plugins_list().get(request.POST.get("plugin_name"))

        if form.is_valid():
            job = obj.enqueue(
                obj.get_env().uninstall_plugin, request, app_id=plugin["plugin_id"]
            )

            messages.success(request, utils.job_msg(job))
            return redirect("core:job", pk=job.pk)

        return render(
            request,
            self.template_name,
            {
                "object": obj,
                "plugin": plugin,
                "form": form,
                "return_url": self.get_return_url(request, obj),
                **self.get_extra_context(request, obj),
            },
        )
