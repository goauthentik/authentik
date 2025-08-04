"""authentik administration overview"""

from django.core.cache import cache
from django_tenants.utils import get_public_schema_name
from drf_spectacular.utils import extend_schema
from packaging.version import parse
from rest_framework.fields import SerializerMethodField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik import __version__, get_build_hash
from authentik.admin.tasks import VERSION_CACHE_KEY, VERSION_NULL, update_latest_version
from authentik.core.api.utils import PassiveSerializer
from authentik.outposts.models import Outpost
from authentik.tenants.utils import get_current_tenant


class VersionSerializer(PassiveSerializer):
    """Get running and latest version."""

    version_current = SerializerMethodField()
    version_latest = SerializerMethodField()
    version_latest_valid = SerializerMethodField()
    build_hash = SerializerMethodField()
    outdated = SerializerMethodField()
    outpost_outdated = SerializerMethodField()

    def get_build_hash(self, _) -> str:
        """Get build hash, if version is not latest or released"""
        return get_build_hash()

    def get_version_current(self, _) -> str:
        """Get current version"""
        return __version__

    def get_version_latest(self, _) -> str:
        """Get latest version from cache"""
        if get_current_tenant().schema_name == get_public_schema_name():
            return __version__
        version_in_cache = cache.get(VERSION_CACHE_KEY)
        if not version_in_cache:  # pragma: no cover
            update_latest_version.send()
            return __version__
        return version_in_cache

    def get_version_latest_valid(self, _) -> bool:
        """Check if latest version is valid"""
        return cache.get(VERSION_CACHE_KEY) != VERSION_NULL

    def get_outdated(self, instance) -> bool:
        """Check if we're running the latest version"""
        return parse(self.get_version_current(instance)) < parse(self.get_version_latest(instance))

    def get_outpost_outdated(self, _) -> bool:
        """Check if any outpost is outdated/has a version mismatch"""
        any_outdated = False
        for outpost in Outpost.objects.all():
            for state in outpost.state:
                if state.version_outdated:
                    any_outdated = True
        return any_outdated


class VersionView(APIView):
    """Get running and latest version."""

    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = []

    @extend_schema(responses={200: VersionSerializer(many=False)})
    def get(self, request: Request) -> Response:
        """Get running and latest version."""
        return Response(VersionSerializer(True).data)
