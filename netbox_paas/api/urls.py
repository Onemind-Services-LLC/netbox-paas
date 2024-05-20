from netbox.api.routers import NetBoxRouter

from . import views

app_name = "netbox_paas"

router = NetBoxRouter()
router.register("configurations", views.NetBoxConfigurationViewSet)
router.register("db-backups", views.NetBoxDBBackupViewSet)
router.register("plugins", views.NetBoxPluginViewSet, basename="plugins")

urlpatterns = router.urls
