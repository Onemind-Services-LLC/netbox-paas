from netbox.api.viewsets import NetBoxModelViewSet
from .serializers import *
from ..models import *


class NetBoxConfigurationViewSet(NetBoxModelViewSet):
    queryset = NetBoxConfiguration.objects.all()
    serializer_class = NetBoxConfigurationSerializer


class NetBoxDBBackupViewSet(NetBoxModelViewSet):
    queryset = NetBoxDBBackup.objects.all()
    serializer_class = NetBoxDBBackupSerializer
