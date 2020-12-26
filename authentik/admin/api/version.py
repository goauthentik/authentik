"""authentik administration overview"""
from django.core.cache import cache
from django.db.models import Model
from drf_yasg2.utils import swagger_auto_schema
from packaging.version import parse
from rest_framework.fields import SerializerMethodField
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from authentik import __version__
from authentik.admin.tasks import VERSION_CACHE_KEY, update_latest_version


class VersionSerializer(Serializer):
    """Get running and latest version."""

    version_current = SerializerMethodField()
    version_latest = SerializerMethodField()
    outdated = SerializerMethodField()

    def get_version_current(self, _) -> str:
        """Get current version"""
        return __version__

    def get_version_latest(self, _) -> str:
        """Get latest version from cache"""
        version_in_cache = cache.get(VERSION_CACHE_KEY)
        if not version_in_cache:  # pragma: no cover
            update_latest_version.delay()
            return __version__
        return version_in_cache

    def get_outdated(self, instance) -> bool:
        """Check if we're running the latest version"""
        return parse(self.get_version_current(instance)) < parse(
            self.get_version_latest(instance)
        )

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class VersionViewSet(ListModelMixin, GenericViewSet):
    """Get running and latest version."""

    permission_classes = [IsAdminUser]

    def get_queryset(self):  # pragma: no cover
        return None

    @swagger_auto_schema(responses={200: VersionSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """Get running and latest version."""
        return Response(VersionSerializer(True).data)
