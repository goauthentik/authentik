"""authentik administration metrics"""
from datetime import timedelta

from django.db.models.functions import ExtractHour
from drf_spectacular.utils import extend_schema, extend_schema_field
from guardian.shortcuts import get_objects_for_user
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.core.api.utils import PassiveSerializer
from authentik.events.models import EventAction


class CoordinateSerializer(PassiveSerializer):
    """Coordinates for diagrams"""

    x_cord = IntegerField(read_only=True)
    y_cord = IntegerField(read_only=True)


class LoginMetricsSerializer(PassiveSerializer):
    """Login Metrics per 1h"""

    logins = SerializerMethodField()
    logins_failed = SerializerMethodField()
    authorizations = SerializerMethodField()

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins(self, _):
        """Get successful logins per 8 hours for the last 7 days"""
        user = self.context["user"]
        return (
            get_objects_for_user(user, "authentik_events.view_event").filter(
                action=EventAction.LOGIN
            )
            # 3 data points per day, so 8 hour spans
            .get_events_per(timedelta(days=7), ExtractHour, 7 * 3)
        )

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins_failed(self, _):
        """Get failed logins per 8 hours for the last 7 days"""
        user = self.context["user"]
        return (
            get_objects_for_user(user, "authentik_events.view_event").filter(
                action=EventAction.LOGIN_FAILED
            )
            # 3 data points per day, so 8 hour spans
            .get_events_per(timedelta(days=7), ExtractHour, 7 * 3)
        )

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_authorizations(self, _):
        """Get successful authorizations per 8 hours for the last 7 days"""
        user = self.context["user"]
        return (
            get_objects_for_user(user, "authentik_events.view_event").filter(
                action=EventAction.AUTHORIZE_APPLICATION
            )
            # 3 data points per day, so 8 hour spans
            .get_events_per(timedelta(days=7), ExtractHour, 7 * 3)
        )


class AdministrationMetricsViewSet(APIView):
    """Login Metrics per 1h"""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: LoginMetricsSerializer(many=False)})
    def get(self, request: Request) -> Response:
        """Login Metrics per 1h"""
        serializer = LoginMetricsSerializer(True)
        serializer.context["user"] = request.user
        return Response(serializer.data)
