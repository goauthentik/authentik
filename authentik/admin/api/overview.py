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
from authentik.core.models import Provider
from authentik.policies.models import Policy
from authentik.root.celery import CELERY_APP


class AdministrationOverviewSerializer(Serializer):
    """Overview View"""

    version = SerializerMethodField()
    version_latest = SerializerMethodField()
    worker_count = SerializerMethodField()
    providers_without_application = SerializerMethodField()
    policies_without_binding = SerializerMethodField()
    cached_policies = SerializerMethodField()
    cached_flows = SerializerMethodField()

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

    def get_providers_without_application(self, _) -> int:
        """Count of providers without application"""
        return len(Provider.objects.filter(application=None))

    def get_policies_without_binding(self, _) -> int:
        """Count of policies not bound or use in prompt stages"""
        return len(
            Policy.objects.filter(bindings__isnull=True, promptstage__isnull=True)
        )

    def get_cached_policies(self, _) -> int:
        """Get cached policy count"""
        return len(cache.keys("policy_*"))

    def get_cached_flows(self, _) -> int:
        """Get cached flow count"""
        return len(cache.keys("flow_*"))

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class AdministrationOverviewViewSet(ViewSet):
    """Return single instance of AdministrationOverviewSerializer"""

    permission_classes = [IsAdminUser]

    @swagger_auto_schema(responses={200: AdministrationOverviewSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """Return single instance of AdministrationOverviewSerializer"""
        serializer = AdministrationOverviewSerializer(True)
        return Response(serializer.data)
