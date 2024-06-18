import random
import string
from importlib.metadata import metadata

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.generic import View

from netbox.views import generic
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
            return redirect("plugins:netbox_paas:netboxconfiguration", pk=obj.pk)

        return redirect("plugins:netbox_paas:netboxconfiguration_add")


@register_model_view(models.NetBoxConfiguration, "edit")
class NetBoxConfigurationEditView(generic.ObjectEditView):
    queryset = models.NetBoxConfiguration.objects.all()
    form = forms.NetBoxConfigurationForm


@register_model_view(models.NetBoxConfiguration, "logs")
class NetBoxNodeLog(PermissionRequiredMixin, View):
    def get_permission_required(self):
        return ["netbox_paas.view_netboxconfiguration"]

    def post(self, request, pk):
        """
        Retrieve logs from Jelastic and return them as a response.
        """
        instance = get_object_or_404(models.NetBoxConfiguration, pk=pk)
        env_name = request.POST.get("env_name")
        node_id = request.POST.get("node_id")

        paas = instance.paas(env_name)

        node = paas.get_node(node_id)
        logs = paas.get_node_log(node_id)
        return render(
            request,
            "netbox_paas/nodelogs.html",
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
        return ["netbox_paas.change_netboxconfiguration"]

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
                    "plugins:netbox_paas:netboxconfiguration",
                    kwargs={"pk": obj.pk},
                ),
            },
        )

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(models.NetBoxConfiguration, pk=kwargs["pk"])

        form = forms.NetBoxSettingsForm(request.POST, initial=obj.netbox_settings())
        if form.is_valid():
            # Call Jelastic to apply the ENV_VARs on all NetBox nodes (including workers)
            job = obj.enqueue(
                obj.apply_settings,
                request,
                data=form.cleaned_data,
            )
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


@register_model_view(models.NetBoxConfiguration, "restart")
class NetBoxRestartView(PermissionRequiredMixin, View):
    def get_permission_required(self):
        return ["netbox_paas.change_netboxconfiguration"]

    def post(self, request, pk):
        """
        Restarts container by node group.
        """
        instance = get_object_or_404(models.NetBoxConfiguration, pk=pk)
        env_name = request.POST.get("env_name")
        node_group = request.POST.get("node_group")
        job = instance.enqueue(
            instance.paas(env_name, auto_init=False).restart_nodes,
            request,
            node_groups=[node_group],
        )
        messages.success(request, utils.job_msg(job))
        return redirect("plugins:netbox_paas:netboxconfiguration", pk=instance.pk)


@register_model_view(models.NetBoxConfiguration, "backup_storage", path="backup-storage")
class NetBoxStorageView(PermissionRequiredMixin, GetReturnURLMixin, View):
    def get_permission_required(self):
        return ["netbox_paas.view_netboxconfiguration"]

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
                    "plugins:netbox_paas:netboxconfiguration",
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
                obj.paas(env_name, auto_init=False).client.marketplace.App.Install,
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
            return redirect("plugins:netbox_paas:netboxdbbackup", pk=obj.pk)

        return redirect("plugins:netbox_paas:netboxdbbackup_add")


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
        return ["netbox_paas.change_netboxdbbackup"]

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
        return ["netbox_paas.change_netboxdbbackup"]

    def post(self, request, pk):
        """
        Restore a backup.
        """
        instance = get_object_or_404(models.NetBoxDBBackup, pk=pk)
        backup_name = request.POST.get("name")

        job = instance.restore(request, backup_name)
        messages.success(request, utils.job_msg(job))
        return redirect("plugins:netbox_paas:netboxdbbackup", pk=instance.pk)


class NetBoxPluginListView(View):
    def get(self, request):
        if nc := models.NetBoxConfiguration.objects.first():
            installed_plugins = settings.PLUGINS
            installed_plugins = [metadata(plugin).get("Name") for plugin in installed_plugins]

            # Get the list of disabled plugins from NetBox
            disabled_plugins = [
                metadata(plugin).get("Name")
                for plugin in list(nc.get_env().load_plugins(file_name=constants.DISABLED_PLUGINS_FILE_NAME).keys())
            ]

            plugins = utils.get_plugins_list()
            for plugin_name, _ in plugins.items():
                if plugin_name in installed_plugins:
                    plugin_version = metadata(plugin_name).get("Version")
                    if upgrade_available := utils.is_upgrade_available(plugins[plugin_name], plugin_version):
                        plugins[plugin_name].update(
                            {
                                "upgrade_available": upgrade_available,
                                "latest_version": utils.filter_releases(plugins[plugin_name])[0],
                            }
                        )

                    plugins[plugin_name].update(
                        {
                            "installed": True,
                            "current_version": plugin_version,
                        }
                    )
                if plugin_name in disabled_plugins:
                    plugins[plugin_name].update(
                        {"installed": True, "disabled": True, "current_version": metadata(plugin_name).get("Version")}
                    )

            # Divide the plugins into two lists: installed and not installed
            plugins = {
                "installed": {
                    plugin_name: plugin for plugin_name, plugin in plugins.items() if plugin.get("installed")
                },
                "not_installed": {
                    plugin_name: plugin for plugin_name, plugin in plugins.items() if not plugin.get("installed")
                },
            }

            # Divide not installed plugins into two lists: subscription and community
            plugins["not_installed"] = {
                "subscription": {
                    plugin_name: plugin
                    for plugin_name, plugin in plugins["not_installed"].items()
                    if plugin.get("private")
                },
                "community": {
                    plugin_name: plugin
                    for plugin_name, plugin in plugins["not_installed"].items()
                    if not plugin.get("private")
                },
            }

            return render(
                request,
                "netbox_paas/plugins_store.html",
                {"object": nc, "plugins": plugins},
            )

        messages.error(request, "You must configure NetBox first.")
        return redirect("plugins:netbox_paas:netboxconfiguration_add")


@register_model_view(models.NetBoxConfiguration, "upgrades")
class NetBoxPluginUpgradesView(PermissionRequiredMixin, GetReturnURLMixin, View):
    queryset = models.NetBoxConfiguration.objects.all()
    form = forms.NetBoxUpgradeForm

    def get_permission_required(self):
        return ["netbox_paas.change_netboxconfiguration"]

    def get(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(models.NetBoxConfiguration, pk=pk)

        return render(
            request,
            "generic/object_edit.html",
            {
                "object": obj,
                "form": self.form(),
            },
        )

    def post(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(models.NetBoxConfiguration, pk=pk)
        form = self.form(request.POST)

        if form.is_valid():
            job = obj.enqueue(
                obj.get_env().upgrade,
                request,
                version=form.cleaned_data["version"],
                lic=obj.license,
            )
            messages.success(request, utils.job_msg(job))
            return redirect("core:job", pk=job.pk)

        return render(
            request,
            "generic/object_edit.html",
            {
                "object": obj,
                "form": form,
            },
        )


@register_model_view(models.NetBoxConfiguration, "plugin_install", path="plugin-install")
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
            plugin = utils.get_plugins_list().get(form.cleaned_data["name"])

            job = obj.enqueue(
                obj.get_env().install_plugin,
                request,
                plugin=plugin,
                version=form.cleaned_data["version"],
                plugin_settings=form.cleaned_data["configuration"],
                github_token=obj.license,
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


@register_model_view(models.NetBoxConfiguration, "plugin_uninstall", path="plugin-uninstall")
class NetBoxPluginUninstallView(generic.ObjectDeleteView):
    queryset = models.NetBoxConfiguration.objects.all()
    template_name = "netbox_paas/plugin_uninstall.html"

    def get(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        plugin = utils.get_plugins_list().get(request.GET.get("name"))

        if plugin is None:
            messages.error(request, "Plugin not found.")
            return redirect("plugins:netbox_paas:netboxplugin_list")

        form = forms.ConfirmationForm(initial=request.GET)

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

    def post(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        form = forms.ConfirmationForm(request.POST)

        if form.is_valid():
            plugin = utils.get_plugins_list().get(form.cleaned_data["name"])
            job = obj.enqueue(obj.get_env().uninstall_plugin, request, plugin=plugin)

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


@register_model_view(models.NetBoxConfiguration, "plugin_enable", path="plugin-enable")
class NetBoxPluginEnableView(generic.ObjectDeleteView):
    queryset = models.NetBoxConfiguration.objects.all()
    template_name = "netbox_paas/plugin_enable.html"

    def get(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        plugin = utils.get_plugins_list().get(request.GET.get("name"))

        if plugin is None:
            messages.error(request, "Plugin not found.")
            return redirect("plugins:netbox_paas:netboxplugin_list")

        form = forms.ConfirmationForm(initial=request.GET)

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

    def post(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        form = forms.ConfirmationForm(request.POST)

        if form.is_valid():
            plugin = utils.get_plugins_list().get(form.cleaned_data["name"])
            job = obj.enqueue(obj.get_env().enable_plugin, request, plugin=plugin)

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


@register_model_view(models.NetBoxConfiguration, "plugin_disable", path="plugin-disable")
class NetBoxPluginDisableView(generic.ObjectDeleteView):
    queryset = models.NetBoxConfiguration.objects.all()
    template_name = "netbox_paas/plugin_disable.html"

    def get(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        plugin = utils.get_plugins_list().get(request.GET.get("name"))

        if plugin is None:
            messages.error(request, "Plugin not found.")
            return redirect("plugins:netbox_paas:netboxplugin_list")

        form = forms.ConfirmationForm(initial=request.GET)

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

    def post(self, request, *args, **kwargs):
        obj = self.get_object(**kwargs)
        form = forms.ConfirmationForm(request.POST)

        if form.is_valid():
            plugin = utils.get_plugins_list().get(form.cleaned_data["name"])
            job = obj.enqueue(obj.get_env().disable_plugin, request, plugin=plugin)

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
