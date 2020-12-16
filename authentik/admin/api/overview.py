"""authentik administration overview"""
from django.core.cache import cache
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.fields import SerializerMethodField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ViewSet

from authentik import __version__
from authentik.admin.tasks import VERSION_CACHE_KEY, update_latest_version
from authentik.root.celery import CELERY_APP


class AdministrationOverviewSerializer(Serializer):
    """Overview View"""

    version = SerializerMethodField()
    version_latest = SerializerMethodField()
    worker_count = SerializerMethodField()

    def get_version(self, _) -> str:
        """Get current version"""
        return __version__

    def get_version_latest(self, _) -> str:
        """Get latest version from cache"""
        version_in_cache = cache.get(VERSION_CACHE_KEY)
        if not version_in_cache:
            update_latest_version.delay()
            return __version__
        return version_in_cache

    def get_worker_count(self, _) -> int:
        """Ping workers"""
        return len(CELERY_APP.control.ping(timeout=0.5))

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class AdministrationOverviewViewSet(ViewSet):
    """General overview information about authentik."""

    permission_classes = [IsAdminUser]

    @swagger_auto_schema(responses={200: AdministrationOverviewSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """General overview information about authentik."""
        serializer = AdministrationOverviewSerializer(True)
        return Response(serializer.data)
