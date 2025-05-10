"""authentik administration overview"""

import platform
from datetime import datetime
from ssl import OPENSSL_VERSION
from sys import version as python_version
from typing import TypedDict

from cryptography.hazmat.backends.openssl.backend import backend
from django.apps import apps
from django.conf import settings
from django.utils.timezone import now
from django.views.debug import SafeExceptionReporterFilter
from drf_spectacular.utils import extend_schema
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik import get_full_version
from authentik.common.config import CONFIG
from authentik.common.utils.reflection import get_env
from authentik.core.api.utils import PassiveSerializer
from authentik.enterprise.license import LicenseKey
from authentik.rbac.permissions import HasPermission


class RuntimeDict(TypedDict):
    """Runtime information"""

    python_version: str
    environment: str
    architecture: str
    platform: str
    uname: str
    openssl_version: str
    openssl_fips_enabled: bool | None
    authentik_version: str


class SystemInfoSerializer(PassiveSerializer):
    """Get system information."""

    http_headers = SerializerMethodField()
    http_host = SerializerMethodField()
    http_is_secure = SerializerMethodField()
    runtime = SerializerMethodField()
    brand = SerializerMethodField()
    server_time = SerializerMethodField()
    embedded_outpost_disabled = SerializerMethodField()
    embedded_outpost_host = SerializerMethodField()

    def get_http_headers(self, request: Request) -> dict[str, str]:
        """Get HTTP Request headers"""
        headers = {}
        raw_session = request._request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        for key, value in request.META.items():
            if not isinstance(value, str):
                continue
            actual_value = value
            if raw_session is not None and raw_session in actual_value:
                actual_value = actual_value.replace(
                    raw_session, SafeExceptionReporterFilter.cleansed_substitute
                )
            headers[key] = actual_value
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
            "architecture": platform.machine(),
            "authentik_version": get_full_version(),
            "environment": get_env(),
            "openssl_fips_enabled": (
                backend._fips_enabled if LicenseKey.get_total().status().is_valid else None
            ),
            "openssl_version": OPENSSL_VERSION,
            "platform": platform.platform(),
            "python_version": python_version,
            "uname": " ".join(platform.uname()),
        }

    def get_brand(self, request: Request) -> str:
        """Currently active brand"""
        return str(request._request.brand)

    def get_server_time(self, request: Request) -> datetime:
        """Current server time"""
        return now()

    def get_embedded_outpost_disabled(self, request: Request) -> bool:
        """Whether the embedded outpost is disabled"""
        return CONFIG.get_bool("outposts.disable_embedded_outpost", False)

    def get_embedded_outpost_host(self, request: Request) -> str:
        """Get the FQDN configured on the embedded outpost"""
        if not apps.is_installed("authentik.outposts"):
            return ""

        from authentik.outposts.apps import MANAGED_OUTPOST
        from authentik.outposts.models import Outpost

        outposts = Outpost.objects.filter(managed=MANAGED_OUTPOST)
        if not outposts.exists():  # pragma: no cover
            return ""
        return outposts.first().config.authentik_host


class SystemView(APIView):
    """Get system information."""

    permission_classes = [HasPermission("authentik_rbac.view_system_info")]
    pagination_class = None
    filter_backends = []
    serializer_class = SystemInfoSerializer

    @extend_schema(responses={200: SystemInfoSerializer(many=False)})
    def get(self, request: Request) -> Response:
        """Get system information."""
        return Response(SystemInfoSerializer(request).data)

    @extend_schema(responses={200: SystemInfoSerializer(many=False)})
    def post(self, request: Request) -> Response:
        """Get system information."""
        return Response(SystemInfoSerializer(request).data)
