"""Serializer mixin for managed models"""
from django.http.response import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.fields import CharField, DateTimeField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.core.api.utils import PassiveSerializer
from authentik.managed.config_files import ConfigFile


class ManagedSerializer:
    """Managed Serializer"""

    managed = CharField(read_only=True, allow_null=True)


class ConfigFileSerializer(PassiveSerializer):
    """Info about a single configuration file"""

    name = CharField(read_only=True)
    last_applied = DateTimeField(required=False, read_only=True)
    status = CharField(read_only=True)
    message = CharField(read_only=True)


class ConfigFileViewSet(ViewSet):
    """Config-file related operations"""

    permission_classes = [IsAdminUser]
    serializer_class = ConfigFileSerializer

    @extend_schema(
        responses={
            200: ConfigFileSerializer(many=False),
            404: OpenApiResponse(description="Config file not found"),
        }
    )
    # pylint: disable=invalid-name
    def retrieve(self, request: Request, pk=None) -> Response:
        """Get a single config file"""
        task = ConfigFile.by_path(pk)
        if not task:
            raise Http404
        return Response(ConfigFileSerializer(task, many=False).data)

    @extend_schema(responses={200: ConfigFileSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """List config files"""
        files = sorted(ConfigFile.all().values(), key=lambda file: file.path)
        return Response(ConfigFileSerializer(files, many=True).data)
