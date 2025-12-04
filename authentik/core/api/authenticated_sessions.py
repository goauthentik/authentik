"""AuthenticatedSessions API Viewset"""

from typing import TypedDict

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import mixins, serializers
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import CharField, DateTimeField, IPAddressField, ListField, UUIDField
from rest_framework.viewsets import GenericViewSet
from ua_parser import user_agent_parser

from authentik.api.validation import validate
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import AuthenticatedSession
from authentik.events.context_processors.asn import ASN_CONTEXT_PROCESSOR, ASNDict
from authentik.events.context_processors.geoip import GEOIP_CONTEXT_PROCESSOR, GeoIPDict
from authentik.rbac.decorators import permission_required


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


class BulkDeleteSessionSerializer(PassiveSerializer):
    """Serializer for bulk deleting authenticated sessions by user"""

    user_pks = ListField(child=serializers.IntegerField(), help_text="List of user IDs to revoke all sessions for")


class AuthenticatedSessionSerializer(ModelSerializer):
    """AuthenticatedSession Serializer"""

    expires = DateTimeField(source="session.expires", read_only=True)
    last_ip = IPAddressField(source="session.last_ip", read_only=True)
    last_user_agent = CharField(source="session.last_user_agent", read_only=True)
    last_used = DateTimeField(source="session.last_used", read_only=True)

    current = SerializerMethodField()
    user_agent = SerializerMethodField()
    geo_ip = SerializerMethodField()
    asn = SerializerMethodField()

    def get_current(self, instance: AuthenticatedSession) -> bool:
        """Check if session is currently active session"""
        request: Request = self.context["request"]
        return request._request.session.session_key == instance.session.session_key

    def get_user_agent(self, instance: AuthenticatedSession) -> UserAgentDict:
        """Get parsed user agent"""
        return user_agent_parser.Parse(instance.session.last_user_agent)

    def get_geo_ip(self, instance: AuthenticatedSession) -> GeoIPDict | None:  # pragma: no cover
        """Get GeoIP Data"""
        return GEOIP_CONTEXT_PROCESSOR.city_dict(instance.session.last_ip)

    def get_asn(self, instance: AuthenticatedSession) -> ASNDict | None:  # pragma: no cover
        """Get ASN Data"""
        return ASN_CONTEXT_PROCESSOR.asn_dict(instance.session.last_ip)

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
        extra_args = {"uuid": {"read_only": True}}


class AuthenticatedSessionViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """AuthenticatedSession Viewset"""

    lookup_field = "uuid"
    queryset = AuthenticatedSession.objects.select_related("session").all()
    serializer_class = AuthenticatedSessionSerializer
    search_fields = ["user__username", "session__last_ip", "session__last_user_agent"]
    filterset_fields = ["user__username", "session__last_ip", "session__last_user_agent"]
    ordering = ["user__username"]
    owner_field = "user"

    @permission_required("authentik_core.delete_authenticatedsession")
    @extend_schema(
        parameters=[
            OpenApiParameter(
                "user_pks",
                serializers.ListField(child=serializers.IntegerField()),
                description="List of user IDs to revoke all sessions for",
                required=True,
            ),
        ],
        responses={
            200: inline_serializer(
                "BulkDeleteSessionResponse",
                {"deleted": serializers.IntegerField()},
            ),
        },
    )
    @validate(BulkDeleteSessionSerializer, location="query")
    @action(detail=False, methods=["DELETE"], pagination_class=None, filter_backends=[])
    def bulk_delete(self, request: Request, *, query: BulkDeleteSessionSerializer) -> Response:
        """Bulk revoke all sessions for multiple users"""
        user_pks = query.validated_data.get("user_pks", [])
        deleted_count, _ = AuthenticatedSession.objects.filter(user_id__in=user_pks).delete()

        return Response({"deleted": deleted_count}, status=200)
