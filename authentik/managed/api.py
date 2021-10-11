"""Serializer mixin for managed models"""
from django.http.response import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.fields import CharField, DateTimeField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ViewSet

from authentik.managed.models import BlueprintInstance


class ManagedSerializer:
    """Managed Serializer"""

    managed = CharField(read_only=True, allow_null=True)


class BlueprintInstanceSerializer(ModelSerializer):
    """Info about a single configuration file"""

    class Meta:

        model = BlueprintInstance
        fields = [
            "path",
            "context",
            "last_applied",
            "status",
        ]


class BlueprintInstanceViewSet(ModelViewSet):
    """Config-file related operations"""

    permission_classes = [IsAdminUser]
    serializer_class = BlueprintInstanceSerializer
    queryset = BlueprintInstance.objects.all()
