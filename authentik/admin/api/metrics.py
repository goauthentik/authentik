"""authentik administration metrics"""
from drf_spectacular.utils import extend_schema, extend_schema_field
from guardian.shortcuts import get_objects_for_user
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.permissions import IsAdminUser
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

    logins_per_1h = SerializerMethodField()
    logins_failed_per_1h = SerializerMethodField()
    authorizations_per_1h = SerializerMethodField()

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins_per_1h(self, _):
        """Get successful logins per hour for the last 24 hours"""
        user = self.context["user"]
        return (
            get_objects_for_user(user, "authentik_events.view_event")
            .filter(action=EventAction.LOGIN)
            .get_events_per_hour()
        )

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins_failed_per_1h(self, _):
        """Get failed logins per hour for the last 24 hours"""
        user = self.context["user"]
        return (
            get_objects_for_user(user, "authentik_events.view_event")
            .filter(action=EventAction.LOGIN_FAILED)
            .get_events_per_hour()
        )

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_authorizations_per_1h(self, _):
        """Get successful authorizations per hour for the last 24 hours"""
        user = self.context["user"]
        return (
            get_objects_for_user(user, "authentik_events.view_event")
            .filter(action=EventAction.AUTHORIZE_APPLICATION)
            .get_events_per_hour()
        )


class AdministrationMetricsViewSet(APIView):
    """Login Metrics per 1h"""

    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: LoginMetricsSerializer(many=False)})
    def get(self, request: Request) -> Response:
        """Login Metrics per 1h"""
        serializer = LoginMetricsSerializer(True)
        serializer.context["user"] = request.user
        return Response(serializer.data)
