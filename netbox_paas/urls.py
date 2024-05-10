from django.urls import include, path

from utilities.urls import get_model_urls
from . import views

app_name = "netbox_paas"

urlpatterns = (
    # Configurations
    path(
        "configurations/",
        views.NetBoxConfigurationListView.as_view(),
        name="netboxconfiguration_list",
    ),
    path(
        "configurations/add/",
        views.NetBoxConfigurationEditView.as_view(),
        name="netboxconfiguration_add",
    ),
    path(
        "configurations/<int:pk>/",
        include(get_model_urls(app_name, "netboxconfiguration")),
    ),
    # DB Backups
    path(
        "db-backups/",
        views.NetBoxDBBackupListView.as_view(),
        name="netboxdbbackup_list",
    ),
    path(
        "db-backups/add/",
        views.NetBoxDBBackupEditView.as_view(),
        name="netboxdbbackup_add",
    ),
    path(
        "db-backups/<int:pk>/",
        include(get_model_urls(app_name, "netboxdbbackup")),
    ),
    # Plugins
    path(
        "plugins/",
        views.NetBoxPluginListView.as_view(),
        name="netboxplugin_list",
    ),
)
