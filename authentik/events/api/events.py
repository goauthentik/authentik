"""Events API Views"""

from datetime import timedelta

import django_filters
from django.db.models import Count, ExpressionWrapper, F, QuerySet
from django.db.models import DateTimeField as DjangoDateTimeField
from django.db.models.fields.json import KeyTextTransform, KeyTransform
from django.db.models.functions import TruncHour
from django.db.models.query_utils import Q
from django.utils.timezone import now
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import ChoiceField, DateTimeField, DictField, IntegerField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.object_types import TypeCreateSerializer
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.enterprise.reports.api.reports import ExportMixin
from authentik.events.models import Event, EventAction


class EventVolumeSerializer(PassiveSerializer):
    """Count of events of action created on day"""

    action = ChoiceField(choices=EventAction.choices)
    time = DateTimeField()
    count = IntegerField()


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
            "brand",
        ]


class EventTopPerUserSerializer(PassiveSerializer):
    """Response object of Event's top_per_user"""

    application = DictField()
    counted_events = IntegerField()
    unique_users = IntegerField()


class EventsFilter(django_filters.FilterSet):
    """Filter for events"""

    username = django_filters.CharFilter(
        field_name="user", label="Username", method="filter_username"
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
    actions = django_filters.MultipleChoiceFilter(
        field_name="action",
        choices=EventAction.choices,
    )
    brand_name = django_filters.CharFilter(
        field_name="brand",
        lookup_expr="name",
        label="Brand name",
    )

    def filter_username(self, queryset, name, value):
        return queryset.filter(Q(user__username=value) | Q(context__username=value))

    def filter_context_model_pk(self, queryset, name, value):
        """Because we store the PK as UUID.hex,
        we need to remove the dashes that a client may send. We can't use a
        UUIDField for this, as some models might not have a UUID PK"""
        value = str(value).replace("-", "")
        query = Q(context__model__pk=value)
        try:
            query |= Q(context__model__pk=int(value))
        except ValueError:
            pass
        return queryset.filter(query)

    class Meta:
        model = Event
        fields = ["action", "client_ip", "username"]


class EventViewSet(ExportMixin, ModelViewSet):
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

    def get_ql_fields(self):
        from djangoql.schema import DateTimeField, StrField

        from authentik.enterprise.search.fields import ChoiceSearchField, JSONSearchField

        return [
            ChoiceSearchField(Event, "action"),
            StrField(Event, "event_uuid"),
            StrField(Event, "app", suggest_options=True),
            StrField(Event, "client_ip"),
            JSONSearchField(Event, "user", suggest_nested=False),
            JSONSearchField(Event, "brand", suggest_nested=False),
            JSONSearchField(Event, "context", suggest_nested=False),
            DateTimeField(Event, "created", suggest_options=True),
        ]

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
        events = (
            get_objects_for_user(request.user, "authentik_events.view_event")
            .filter(action=filtered_action)
            .exclude(context__authorized_application=None)
            .annotate(application=KeyTransform("authorized_application", "context"))
            .annotate(user_pk=KeyTextTransform("pk", "user"))
            .values("application")
            .annotate(counted_events=Count("application"))
            .annotate(unique_users=Count("user_pk", distinct=True))
            .values("unique_users", "application", "counted_events")
            .order_by("-counted_events")[:top_n]
        )
        return Response(EventTopPerUserSerializer(instance=events, many=True).data)

    @extend_schema(
        responses={200: EventVolumeSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                "history_days",
                type=OpenApiTypes.NUMBER,
                location=OpenApiParameter.QUERY,
                required=False,
                default=7,
            ),
        ],
    )
    @action(detail=False, methods=["GET"], pagination_class=None)
    def volume(self, request: Request) -> Response:
        """Get event volume for specified filters and timeframe"""
        queryset: QuerySet[Event] = self.filter_queryset(self.get_queryset())
        delta = timedelta(days=7)
        time_delta = request.query_params.get("history_days", 7)
        if time_delta:
            delta = timedelta(days=min(int(time_delta), 60))
        return Response(
            queryset.filter(created__gte=now() - delta)
            .annotate(hour=TruncHour("created"))
            .annotate(
                time=ExpressionWrapper(
                    F("hour") - (F("hour__hour") % 6) * timedelta(hours=1),
                    output_field=DjangoDateTimeField(),
                )
            )
            .values("time", "action")
            .annotate(count=Count("pk"))
            .order_by("time", "action")
        )

    @extend_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def actions(self, request: Request) -> Response:
        """Get all actions"""
        data = []
        for value, name in EventAction.choices:
            data.append({"name": name, "description": "", "component": value, "model_name": ""})
        return Response(TypeCreateSerializer(data, many=True).data)
