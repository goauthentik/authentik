"""authentik administration overview"""

from drf_spectacular.utils import extend_schema
from packaging.version import parse
from rest_framework.fields import SerializerMethodField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik import authentik_build_hash, authentik_version
from authentik.admin.tasks import UpdateVersionInfo
from authentik.core.api.utils import PassiveSerializer
from authentik.outposts.models import Outpost


class VersionSerializer(PassiveSerializer):
    """Get running and latest version."""

    version_current = SerializerMethodField()
    version_latest = SerializerMethodField(allow_null=True)
    build_hash = SerializerMethodField()
    outdated = SerializerMethodField()
    outpost_outdated = SerializerMethodField()

    def get_build_hash(self, _) -> str:
        """Get build hash, if version is not latest or released"""
        return authentik_build_hash()

    def get_version_current(self, _) -> str:
        """Get current version"""
        return authentik_version()

    def get_version_latest(self, _) -> UpdateVersionInfo:
        """Get latest version from cache"""
        return UpdateVersionInfo.get_cached().model_dump(mode="json")

    def get_outdated(self, instance) -> bool:
        """Check if we're running the latest version"""
        cached = UpdateVersionInfo.get_cached()
        if not cached:
            return False
        return parse(self.get_version_current(instance)) < parse(cached.version)

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
