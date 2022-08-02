"""Serializer mixin for managed models"""
from glob import glob

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer, ModelSerializer
from rest_framework.viewsets import ModelViewSet
from authentik.core.api.used_by import UsedByMixin

from authentik.blueprints.models import BlueprintInstance
from authentik.lib.config import CONFIG


class ManagedSerializer:
    """Managed Serializer"""

    managed = CharField(read_only=True, allow_null=True)


class BlueprintInstanceSerializer(ModelSerializer):
    """Info about a single blueprint instance file"""

    class Meta:

        model = BlueprintInstance
        fields = [
            "pk",
            "name",
            "path",
            "context",
            "last_applied",
            "last_applied_hash",
            "status",
            "enabled",
            "managed_models",
        ]
        extra_kwargs = {
            "last_applied": {"read_only": True},
            "last_applied_hash": {"read_only": True},
            "managed_models": {"read_only": True},
        }


class BlueprintInstanceViewSet(UsedByMixin, ModelViewSet):
    """Blueprint instances"""

    permission_classes = [IsAdminUser]
    serializer_class = BlueprintInstanceSerializer
    queryset = BlueprintInstance.objects.all()
    search_fields = ["name", "path"]
    filterset_fields = ["name", "path"]

    @extend_schema(responses={200: ListSerializer(child=CharField())})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def available(self, request: Request) -> Response:
        """Get blueprints"""
        files = []
        for folder in CONFIG.y("blueprint_locations"):
            for file in glob(f"{folder}/**", recursive=True):
                files.append(file)
        return Response(files)
