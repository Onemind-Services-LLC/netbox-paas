from django.urls import include, path

from utilities.urls import get_model_urls
from . import views

app_name = "netbox_cloud_pilot"

urlpatterns = (
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
)
