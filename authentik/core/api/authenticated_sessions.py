"""AuthenticatedSessions API Viewset"""
from typing import Optional, TypedDict

from django_filters.rest_framework import DjangoFilterBackend
from guardian.utils import get_anonymous_user
from rest_framework import mixins
from rest_framework.fields import SerializerMethodField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet
from ua_parser import user_agent_parser

from authentik.api.authorization import OwnerSuperuserPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.core.models import AuthenticatedSession
from authentik.events.geo import GEOIP_READER, GeoIPDict


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

    def get_current(self, instance: AuthenticatedSession) -> bool:
        """Check if session is currently active session"""
        request: Request = self.context["request"]
        return request._request.session.session_key == instance.session_key

    def get_user_agent(self, instance: AuthenticatedSession) -> UserAgentDict:
        """Get parsed user agent"""
        return user_agent_parser.Parse(instance.last_user_agent)

    def get_geo_ip(self, instance: AuthenticatedSession) -> Optional[GeoIPDict]:  # pragma: no cover
        """Get parsed user agent"""
        return GEOIP_READER.city_dict(instance.last_ip)

    class Meta:
        model = AuthenticatedSession
        fields = [
            "uuid",
            "current",
            "user_agent",
            "geo_ip",
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
    permission_classes = [OwnerSuperuserPermissions]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)
