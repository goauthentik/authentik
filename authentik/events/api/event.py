"""Events API Views"""
import django_filters
from django.db.models.aggregates import Count
from django.db.models.fields.json import KeyTextTransform
from drf_yasg.utils import swagger_auto_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import CharField, DictField, IntegerField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentik.events.models import Event, EventAction


class EventSerializer(ModelSerializer):
    """Event Serializer"""

    # Since we only use this serializer for read-only operations,
    # no checking of the action is done here.
    # This allows clients to check wildcards, prefixes and custom types
    action = CharField()

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
            "expires",
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


class EventsFilter(django_filters.FilterSet):
    """Filter for events"""

    username = django_filters.CharFilter(
        field_name="user", lookup_expr="username", label="Username"
    )
    context_model_pk = django_filters.CharFilter(
        field_name="context",
        lookup_expr="model__pk",
        label="Context Model Primary Key",
        method="filter_context_model_pk",
    )
    context_model_name = django_filters.CharFilter(
        field_name="context",
        lookup_expr="model__model_name",
        label="Context Model Name",
    )
    context_model_app = django_filters.CharFilter(
        field_name="context", lookup_expr="model__app", label="Context Model App"
    )
    context_authorized_app = django_filters.CharFilter(
        field_name="context",
        lookup_expr="authorized_application__pk",
        label="Context Authorized application",
    )
    action = django_filters.CharFilter(
        field_name="action",
        lookup_expr="icontains",
    )

    # pylint: disable=unused-argument
    def filter_context_model_pk(self, queryset, name, value):
        """Because we store the PK as UUID.hex,
        we need to remove the dashes that a client may send. We can't use a
        UUIDField for this, as some models might not have a UUID PK"""
        value = str(value).replace("-", "")
        return queryset.filter(context__model__pk=value)

    class Meta:
        model = Event
        fields = ["action", "client_ip", "username"]


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
    filterset_class = EventsFilter

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
            get_objects_for_user(request.user, "authentik_events.view_event")
            .filter(action=filtered_action)
            .exclude(context__authorized_application=None)
            .annotate(application=KeyTextTransform("authorized_application", "context"))
            .annotate(user_pk=KeyTextTransform("pk", "user"))
            .values("application")
            .annotate(counted_events=Count("application"))
            .annotate(unique_users=Count("user_pk", distinct=True))
            .values("unique_users", "application", "counted_events")
            .order_by("-counted_events")[:top_n]
        )
