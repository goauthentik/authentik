"""authentik administration overview"""
import platform
from datetime import datetime
from sys import version as python_version
from typing import TypedDict

from django.utils.timezone import now
from drf_spectacular.utils import extend_schema
from gunicorn import version_info as gunicorn_version
from rest_framework.fields import SerializerMethodField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.core.api.utils import PassiveSerializer
from authentik.lib.utils.reflection import get_env
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost


class RuntimeDict(TypedDict):
    """Runtime information"""

    python_version: str
    gunicorn_version: str
    environment: str
    architecture: str
    platform: str
    uname: str


class SystemSerializer(PassiveSerializer):
    """Get system information."""

    http_headers = SerializerMethodField()
    http_host = SerializerMethodField()
    http_is_secure = SerializerMethodField()
    runtime = SerializerMethodField()
    tenant = SerializerMethodField()
    server_time = SerializerMethodField()
    embedded_outpost_host = SerializerMethodField()

    def get_http_headers(self, request: Request) -> dict[str, str]:
        """Get HTTP Request headers"""
        headers = {}
        for key, value in request.META.items():
            if not isinstance(value, str):
                continue
            headers[key] = value
        return headers

    def get_http_host(self, request: Request) -> str:
        """Get HTTP host"""
        return request._request.get_host()

    def get_http_is_secure(self, request: Request) -> bool:
        """Get HTTP Secure flag"""
        return request._request.is_secure()

    def get_runtime(self, request: Request) -> RuntimeDict:
        """Get versions"""
        return {
            "python_version": python_version,
            "gunicorn_version": ".".join(str(x) for x in gunicorn_version),
            "environment": get_env(),
            "architecture": platform.machine(),
            "platform": platform.platform(),
            "uname": " ".join(platform.uname()),
        }

    def get_tenant(self, request: Request) -> str:
        """Currently active tenant"""
        return str(request._request.tenant)

    def get_server_time(self, request: Request) -> datetime:
        """Current server time"""
        return now()

    def get_embedded_outpost_host(self, request: Request) -> str:
        """Get the FQDN configured on the embedded outpost"""
        outposts = Outpost.objects.filter(managed=MANAGED_OUTPOST)
        if not outposts.exists():  # pragma: no cover
            return ""
        return outposts.first().config.authentik_host


class SystemView(APIView):
    """Get system information."""

    permission_classes = [IsAdminUser]
    pagination_class = None
    filter_backends = []
    serializer_class = SystemSerializer

    @extend_schema(responses={200: SystemSerializer(many=False)})
    def get(self, request: Request) -> Response:
        """Get system information."""
        return Response(SystemSerializer(request).data)

    @extend_schema(responses={200: SystemSerializer(many=False)})
    def post(self, request: Request) -> Response:
        """Get system information."""
        return Response(SystemSerializer(request).data)
