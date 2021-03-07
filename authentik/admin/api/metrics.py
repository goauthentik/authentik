"""authentik administration metrics"""
import time
from collections import Counter, namedtuple
from datetime import timedelta

from django.db.models import Count, ExpressionWrapper, F, Model
from django.db.models.fields import DurationField
from django.db.models.functions import ExtractHour
from django.utils.timezone import now
from drf_yasg2.utils import swagger_auto_schema, swagger_serializer_method
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ViewSet

from authentik.events.models import Event, EventAction


def get_events_per_1h(**filter_kwargs) -> list[dict[str, int]]:
    """Get event count by hour in the last day, fill with zeros"""
    date_from = now() - timedelta(days=1)
    result = (
        Event.objects.filter(created__gte=date_from, **filter_kwargs)
        .annotate(
            age=ExpressionWrapper(now() - F("created"), output_field=DurationField())
        )
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
                "x": time.mktime((_now + timedelta(hours=hour)).timetuple()) * 1000,
                "y": data[hour * -1],
            }
        )
    return results


class CoordinateSerializer(Serializer):
    """Coordinates for diagrams"""

    x = IntegerField(read_only=True)
    y = IntegerField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class LoginMetricsSerializer(Serializer):
    """Login Metrics per 1h"""

    logins_per_1h = SerializerMethodField()
    logins_failed_per_1h = SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=CoordinateSerializer(many=True))
    def get_logins_per_1h(self, _):
        """Get successful logins per hour for the last 24 hours"""
        return get_events_per_1h(action=EventAction.LOGIN)

    @swagger_serializer_method(serializer_or_field=CoordinateSerializer(many=True))
    def get_logins_failed_per_1h(self, _):
        """Get failed logins per hour for the last 24 hours"""
        return get_events_per_1h(action=EventAction.LOGIN_FAILED)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class AdministrationMetricsViewSet(ViewSet):
    """Login Metrics per 1h"""

    permission_classes = [IsAdminUser]

    @swagger_auto_schema(responses={200: LoginMetricsSerializer(many=False)})
    def list(self, request: Request) -> Response:
        """Login Metrics per 1h"""
        serializer = LoginMetricsSerializer(True)
        return Response(serializer.data)
