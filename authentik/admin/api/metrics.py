"""authentik administration metrics"""
import time
from collections import Counter
from datetime import timedelta

from django.db.models import Count, ExpressionWrapper, F
from django.db.models.fields import DurationField
from django.db.models.functions import ExtractHour
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.core.api.utils import PassiveSerializer
from authentik.events.models import Event, EventAction


def get_events_per_1h(**filter_kwargs) -> list[dict[str, int]]:
    """Get event count by hour in the last day, fill with zeros"""
    date_from = now() - timedelta(days=1)
    result = (
        Event.objects.filter(created__gte=date_from, **filter_kwargs)
        .annotate(age=ExpressionWrapper(now() - F("created"), output_field=DurationField()))
        .annotate(age_hours=ExtractHour("age"))
        .values("age_hours")
        .annotate(count=Count("pk"))
        .order_by("age_hours")
    )
    data = Counter({int(d["age_hours"]): d["count"] for d in result})
    results = []
    _now = now()
    for hour in range(0, -24, -1):
        results.append(
            {
                "x_cord": time.mktime((_now + timedelta(hours=hour)).timetuple()) * 1000,
                "y_cord": data[hour * -1],
            }
        )
    return results


class CoordinateSerializer(PassiveSerializer):
    """Coordinates for diagrams"""

    x_cord = IntegerField(read_only=True)
    y_cord = IntegerField(read_only=True)


class LoginMetricsSerializer(PassiveSerializer):
    """Login Metrics per 1h"""

    logins_per_1h = SerializerMethodField()
    logins_failed_per_1h = SerializerMethodField()

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins_per_1h(self, _):
        """Get successful logins per hour for the last 24 hours"""
        return get_events_per_1h(action=EventAction.LOGIN)

    @extend_schema_field(CoordinateSerializer(many=True))
    def get_logins_failed_per_1h(self, _):
        """Get failed logins per hour for the last 24 hours"""
        return get_events_per_1h(action=EventAction.LOGIN_FAILED)


class AdministrationMetricsViewSet(APIView):
    """Login Metrics per 1h"""

    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: LoginMetricsSerializer(many=False)})
    def get(self, request: Request) -> Response:
        """Login Metrics per 1h"""
        serializer = LoginMetricsSerializer(True)
        return Response(serializer.data)
