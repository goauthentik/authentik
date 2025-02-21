"""AuthenticatedSessions API Viewset"""

from typing import TypedDict

from rest_framework import mixins
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet
from ua_parser import user_agent_parser

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import AuthenticatedSession
from authentik.events.context_processors.asn import ASN_CONTEXT_PROCESSOR, ASNDict
from authentik.events.context_processors.geoip import GEOIP_CONTEXT_PROCESSOR, GeoIPDict


class UserAgentDeviceDict(TypedDict):
    """User agent device"""

    brand: str
    family: str
    model: str


class UserAgentOSDict(TypedDict):
    """User agent os"""

    family: str
    major: str
    minor: str
    patch: str
    patch_minor: str


class UserAgentBrowserDict(TypedDict):
    """User agent browser"""

    family: str
    major: str
    minor: str
    patch: str


class UserAgentDict(TypedDict):
    """User agent details"""

    device: UserAgentDeviceDict
    os: UserAgentOSDict
    user_agent: UserAgentBrowserDict
    string: str


class AuthenticatedSessionSerializer(ModelSerializer):
    """AuthenticatedSession Serializer"""

    current = SerializerMethodField()
    user_agent = SerializerMethodField()
    geo_ip = SerializerMethodField()
    asn = SerializerMethodField()

    def get_current(self, instance: AuthenticatedSession) -> bool:
        """Check if session is currently active session"""
        request: Request = self.context["request"]
        return request._request.session.session_key == instance.session_key

    def get_user_agent(self, instance: AuthenticatedSession) -> UserAgentDict:
        """Get parsed user agent"""
        return user_agent_parser.Parse(instance.last_user_agent)

    def get_geo_ip(self, instance: AuthenticatedSession) -> GeoIPDict | None:  # pragma: no cover
        """Get GeoIP Data"""
        return GEOIP_CONTEXT_PROCESSOR.city_dict(instance.last_ip)

    def get_asn(self, instance: AuthenticatedSession) -> ASNDict | None:  # pragma: no cover
        """Get ASN Data"""
        return ASN_CONTEXT_PROCESSOR.asn_dict(instance.last_ip)

    class Meta:
        model = AuthenticatedSession
        fields = [
            "uuid",
            "current",
            "user_agent",
            "geo_ip",
            "asn",
            "user",
            "last_ip",
            "last_user_agent",
            "last_used",
            "expires",
        ]


class AuthenticatedSessionViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """AuthenticatedSession Viewset"""

    queryset = AuthenticatedSession.objects.all()
    serializer_class = AuthenticatedSessionSerializer
    search_fields = ["user__username", "last_ip", "last_user_agent"]
    filterset_fields = ["user__username", "last_ip", "last_user_agent"]
    ordering = ["user__username"]
    owner_field = "user"
