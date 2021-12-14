"""Events API Views"""
from json import loads

import django_filters
from django.db.models.aggregates import Count
from django.db.models.fields.json import KeyTextTransform
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import DictField, IntegerField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.admin.api.metrics import CoordinateSerializer
from authentik.core.api.utils import PassiveSerializer, TypeCreateSerializer
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
            "expires",
            "tenant",
        ]


class EventTopPerUserSerializer(PassiveSerializer):
    """Response object of Event's top_per_user"""

    application = DictField()
    counted_events = IntegerField()
    unique_users = IntegerField()


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
    tenant_name = django_filters.CharFilter(
        field_name="tenant",
        lookup_expr="name",
        label="Tenant name",
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


class EventViewSet(ModelViewSet):
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

    @extend_schema(
        methods=["GET"],
        responses={200: EventTopPerUserSerializer(many=True)},
        filters=[],
        parameters=[
            OpenApiParameter(
                "action",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                "top_n",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
    )
    @action(detail=False, methods=["GET"], pagination_class=None)
    def top_per_user(self, request: Request):
        """Get the top_n events grouped by user count"""
        filtered_action = request.query_params.get("action", EventAction.LOGIN)
        top_n = int(request.query_params.get("top_n", "15"))
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

    @extend_schema(
        methods=["GET"],
        responses={200: CoordinateSerializer(many=True)},
        filters=[],
        parameters=[
            OpenApiParameter(
                "action",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                "query",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
    )
    @action(detail=False, methods=["GET"], pagination_class=None)
    def per_month(self, request: Request):
        """Get the count of events per month"""
        filtered_action = request.query_params.get("action", EventAction.LOGIN)
        try:
            query = loads(request.query_params.get("query", "{}"))
        except ValueError:
            return Response(status=400)
        return Response(
            get_objects_for_user(request.user, "authentik_events.view_event")
            .filter(action=filtered_action)
            .filter(**query)
            .get_events_per_day()
        )

    @extend_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def actions(self, request: Request) -> Response:
        """Get all actions"""
        data = []
        for value, name in EventAction.choices:
            data.append({"name": name, "description": "", "component": value, "model_name": ""})
        return Response(TypeCreateSerializer(data, many=True).data)
