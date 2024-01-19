from django.conf import settings
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from core.api.serializers import JobSerializer
from netbox.api.viewsets import NetBoxModelViewSet
from utilities.rqworker import get_workers_for_queue
from .serializers import *
from ..models import *
from ..utils import get_plugins_list


class NetBoxConfigurationViewSet(NetBoxModelViewSet):
    queryset = NetBoxConfiguration.objects.all()
    serializer_class = NetBoxConfigurationSerializer


class NetBoxDBBackupViewSet(NetBoxModelViewSet):
    queryset = NetBoxDBBackup.objects.all()
    serializer_class = NetBoxDBBackupSerializer


class NetBoxPluginViewSet(ViewSet):
    queryset = NetBoxConfiguration.objects.all()

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.netbox_configuration = NetBoxConfiguration.objects.first()
        if not self.netbox_configuration:
            raise ValidationError("NetBoxConfiguration object not found.")

        # Get plugins list
        self.plugins = get_plugins_list()

    def check_actions(self):
        # Check if RQ worker is running
        if not get_workers_for_queue('default'):
            raise ValidationError(
                "No RQ workers operating on the 'default' queue are currently active in the environment."
            )

        # Check if there are active actions in the environment
        if self.netbox_configuration.get_env().get_actions():
            raise ValidationError("There are currently actions running on the environment.")

    @extend_schema(
        responses={200: NetBoxPluginSerializer(many=True)},
    )
    def list(self, request):
        # Get plugins list
        plugins_list = []

        for plugin_id, plugin in self.plugins.items():
            plugins_list.append({**plugin, 'plugin_id': plugin_id})

        data = NetBoxPluginSerializer(
            plugins_list, many=True, context={'plugins': self.plugins, 'request': request}
        ).data
        return Response({'results': data, 'count': len(data)})

    @extend_schema(
        responses={200: NetBoxPluginSerializer},
        description="Get a plugin object.",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Plugin ID",
            ),
        ],
    )
    def retrieve(self, request, pk=None):
        # Get plugins list
        plugin = self.plugins.get(pk)
        if not plugin:
            raise ValidationError("Plugin not found.")

        data = NetBoxPluginSerializer(
            {
                **plugin,
                'plugin_id': pk,
            },
            context={'plugins': self.plugins, 'request': request},
        ).data
        return Response(data)

    @extend_schema(
        request=NetBoxPluginInstallSerializer,
        responses={200: JobSerializer},
        description="Update a plugin.",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Plugin ID",
            ),
        ],
    )
    def update(self, request, pk=None):
        plugin = self.plugins.get(pk)
        serializer = NetBoxPluginInstallSerializer(
            data=request.data, context={'plugins': self.plugins, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        self.check_actions()

        job = self.netbox_configuration.enqueue(
            self.netbox_configuration.get_env().install_plugin,
            request,
            plugin=plugin,
            version=serializer.validated_data["version"],
            plugin_settings=serializer.validated_data.get("configuration"),
            github_token=self.netbox_configuration.license,
        )

        return Response(JobSerializer(job, context={'request': request}).data)

    @extend_schema(
        responses={200: JobSerializer},
        description="Uninstall a plugin.",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Plugin ID",
            ),
        ],
    )
    def destroy(self, request, pk=None):
        plugin = self.plugins.get(pk)
        if not plugin:
            raise ValidationError("Plugin not found.")

        if plugin['app_label'] not in settings.PLUGINS:
            raise ValidationError(f"Plugin {pk} is not installed.")

        self.check_actions()

        job = self.netbox_configuration.enqueue(
            self.netbox_configuration.get_env().uninstall_plugin,
            request,
            plugin=plugin,
        )

        return Response(JobSerializer(job, context={'request': request}).data)

    @extend_schema(
        request=NetBoxPluginInstallSerializer,
        responses={200: JobSerializer},
    )
    def create(self, request):
        serializer = NetBoxPluginInstallSerializer(
            data=request.data, context={'plugins': self.plugins, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        self.check_actions()

        plugin = self.plugins.get(serializer.validated_data["plugin_id"])
        job = self.netbox_configuration.enqueue(
            self.netbox_configuration.get_env().install_plugin,
            request,
            plugin=plugin,
            version=serializer.validated_data["version"],
            plugin_settings=serializer.validated_data.get("configuration"),
            github_token=self.netbox_configuration.license,
        )
        return Response(JobSerializer(job, context={'request': request}).data)
