"""Events API Views"""
from django.db.models.aggregates import Count
from django.db.models.fields.json import KeyTextTransform
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import DictField, IntegerField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.events.models import Event, EventAction


class EventSerializer(ModelSerializer):
    """Event Serializer"""

    class Meta:

        model = Event
        fields = [
            "pk",
            "user",
            "action",
            "app",
            "context",
            "client_ip",
            "created",
        ]


class EventTopPerUserParams(Serializer):
    """Query params for top_per_user"""

    top_n = IntegerField(default=15)

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class EventTopPerUserSerializer(Serializer):
    """Response object of Event's top_per_user"""

    application = DictField()
    counted_events = IntegerField()
    unique_users = IntegerField()

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class EventViewSet(ReadOnlyModelViewSet):
    """Event Read-Only Viewset"""

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    ordering = ["-created"]
    search_fields = [
        "event_uuid",
        "user",
        "action",
        "app",
        "context",
        "client_ip",
    ]
    filterset_fields = ["action"]

    @swagger_auto_schema(
        method="GET",
        responses={200: EventTopPerUserSerializer(many=True)},
        query_serializer=EventTopPerUserParams,
    )
    @action(detail=False, methods=["GET"])
    def top_per_user(self, request: Request):
        """Get the top_n events grouped by user count"""
        filtered_action = request.query_params.get("action", EventAction.LOGIN)
        top_n = request.query_params.get("top_n", 15)
        return Response(
            Event.objects.filter(action=filtered_action)
            .exclude(context__authorized_application=None)
            .annotate(application=KeyTextTransform("authorized_application", "context"))
            .annotate(user_pk=KeyTextTransform("pk", "user"))
            .values("application")
            .annotate(counted_events=Count("application"))
            .annotate(unique_users=Count("user_pk", distinct=True))
            .values("unique_users", "application", "counted_events")
            .order_by("-counted_events")[:top_n]
        )
