"""Serializer mixin for managed models"""
from glob import glob
from pathlib import Path

from django.http.response import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, DateTimeField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer, ModelSerializer
from rest_framework.viewsets import ModelViewSet, ViewSet

from authentik.core.api.utils import TypeCreateSerializer
from authentik.lib.config import CONFIG
from authentik.managed.models import BlueprintInstance


class ManagedSerializer:
    """Managed Serializer"""

    managed = CharField(read_only=True, allow_null=True)


class BlueprintInstanceSerializer(ModelSerializer):
    """Info about a single blueprint instance file"""

    class Meta:

        model = BlueprintInstance
        fields = [
            "path",
            "context",
            "last_applied",
            "status",
        ]


class BlueprintInstanceViewSet(ModelViewSet):
    """Blueprint instances"""

    permission_classes = [IsAdminUser]
    serializer_class = BlueprintInstanceSerializer
    queryset = BlueprintInstance.objects.all()

    @extend_schema(responses={200: ListSerializer(child=CharField())})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def available(self, request: Request) -> Response:
        files = []
        for folder in CONFIG.y("blueprint_locations"):
            for file in glob(f"{folder}/**", recursive=True):
                files.append(file)
        return Response(files)
