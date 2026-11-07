"""Events API Views"""

from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from json import loads

import django_filters
from django.core.exceptions import EmptyResultSet
from django.db import connections
from django.db.models import Count, Func, QuerySet, TextField, Value
from django.db.models import DateTimeField as DjangoDateTimeField
from django.db.models.fields.json import KeyTextTransform, KeyTransform
from django.db.models.functions import Cast, Collate
from django.db.models.query_utils import Q
from django.utils.text import slugify
from django.utils.timezone import now
from djangoql.schema import DateTimeField as QLDateTimeFIeld
from djangoql.schema import IntField, StrField
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import (
    CharField,
    ChoiceField,
    DateTimeField,
    DictField,
    IntegerField,
    ListField,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.api.search.fields import ChoiceSearchField, IndexedStrField, JSONSearchField
from authentik.api.validation import validate
from authentik.core.api.object_types import TypeCreateSerializer
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.lib.utils.db import distinct_values
from authentik.lib.utils.reflection import ConditionalInheritance
from authentik.lib.utils.time import timedelta_from_string, timedelta_string_validator

AGGR_MAX_AGE = timedelta(days=90)


class EventVolumeSerializer(PassiveSerializer):
    """Count of events of action created on day for a single event action"""

    action = ChoiceField(choices=EventAction.choices)
    time = DateTimeField()
    count = IntegerField()


class EventStatsSerializer(PassiveSerializer):
    """Count of unique users in events and aggregated counts per specified deltas"""

    unique_users = IntegerField()
    count_step = DictField()


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
    context_device = django_filters.CharFilter(
        field_name="context",
        lookup_expr="device__pk",
        label="Context Device Primary Key",
    )
    action = django_filters.CharFilter(field_name="action", method="filter_action")
    actions = django_filters.MultipleChoiceFilter(
        field_name="action",
        choices=EventAction.choices,
        # A filter on a column of the event itself cannot return an event twice
        distinct=False,
    )
    brand_name = django_filters.CharFilter(
        field_name="brand",
        lookup_expr="name",
        label="Brand name",
    )

    def filter_action(self, queryset, name, value):
        """Match actions containing `value`, ignoring case. A substring match cannot use the
        action index, so find the few distinct actions that contain `value` and filter on
        those instead."""
        value = value.upper()
        actions = [
            action
            for action in distinct_values(Event.objects.all(), "action")
            if value in action.upper()
        ]
        return queryset.filter(action__in=actions)

    def filter_username(self, queryset, name, value):
        query = Q(user__username=value) | Q(context__username=value)
        user_pk = User.objects.filter(username=value).values_list("pk", flat=True).first()
        if user_pk is not None:
            query |= Q(
                context__model__app=User._meta.app_label,
                context__model__model_name=User._meta.model_name,
                context__model__pk=user_pk,
            )
        return queryset.filter(query)

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


class EventViewSet(
    ConditionalInheritance("authentik.enterprise.reports.api.reports.ExportMixin"), ModelViewSet
):
    """Event Read-Only Viewset"""

    class EventVolumeParameters(PassiveSerializer):
        history_days = IntegerField(default=7, required=False)

    class EventStatsParameters(PassiveSerializer):
        count_steps = ListField(
            child=CharField(validators=[timedelta_string_validator]),
            required=True,
            help_text="Timedelta, format of 'weeks=3;days=2;hours=3,seconds=2'",
        )

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
        return [
            ChoiceSearchField(Event, "action"),
            StrField(Event, "event_uuid"),
            IndexedStrField(Event, "app"),
            StrField(Event, "client_ip"),
            JSONSearchField(
                Event,
                "user",
                fixed_structure=OrderedDict(
                    pk=IntField(),
                    username=StrField(),
                    email=StrField(),
                ),
            ),
            JSONSearchField(
                Event,
                "brand",
                fixed_structure=OrderedDict(
                    pk=StrField(),
                    app=StrField(),
                    name=StrField(),
                    model_name=StrField(),
                ),
            ),
            JSONSearchField(
                Event,
                "context",
                fixed_structure=OrderedDict(
                    http_request=JSONSearchField(
                        Event,
                        "context_http_request",
                        fixed_structure=OrderedDict(
                            args=JSONSearchField(Event, "context_http_request_args"),
                            path=StrField(),
                            method=StrField(),
                            request_id=StrField(),
                            user_agent=StrField(),
                        ),
                    ),
                ),
            ),
            QLDateTimeFIeld(Event, "created", suggest_options=True),
        ]

    class TopPerUserSerializer(PassiveSerializer):
        top_n = IntegerField(default=15)

    @extend_schema(
        methods=["GET"],
        responses={200: EventTopPerUserSerializer(many=True)},
        parameters=[TopPerUserSerializer],
    )
    @validate(TopPerUserSerializer, location="query")
    @action(detail=False, methods=["GET"], pagination_class=None)
    def top_per_user(self, request: Request, query: TopPerUserSerializer):
        """Get the top_n events grouped by user count"""
        top_n = query.validated_data.get("top_n")
        # Counting distinct users per application in one pass makes Postgres sort every
        # event with its whole context. Instead, count the events of each application and
        # user pair, then add up the pairs of each application. The pairs carry only the two
        # keys, compared as C-collated text, so sorting them is far cheaper.
        pairs = (
            self.filter_queryset(self.get_queryset())
            .exclude(context__authorized_application=None)
            .values(
                application=Collate(
                    Cast(KeyTransform("authorized_application", "context"), TextField()), "C"
                ),
                user_pk=Collate(KeyTextTransform("pk", "user"), "C"),
            )
            .annotate(events=Count("pk"))
            .order_by()
        )
        try:
            pairs_sql, params = pairs.query.get_compiler(pairs.db).as_sql()
        except EmptyResultSet:
            # The filters cannot match anything, such as an action no event has
            return Response([])
        with connections[pairs.db].cursor() as cursor:
            cursor.execute(
                f"""
                SELECT application, SUM(events), COUNT(user_pk)
                FROM ({pairs_sql}) AS pairs
                GROUP BY application
                ORDER BY 2 DESC
                LIMIT %s
                """,  # nosec: pairs_sql is compiled by Django and its values are in params
                (*params, top_n),
            )
            events = [
                {"application": loads(application), "counted_events": count, "unique_users": users}
                for application, count, users in cursor.fetchall()
            ]
        return Response(EventTopPerUserSerializer(instance=events, many=True).data)

    @extend_schema(
        responses={200: EventVolumeSerializer(many=True)},
        parameters=[EventVolumeParameters],
    )
    @action(detail=False, methods=["GET"], pagination_class=None)
    @validate(EventVolumeParameters, "query")
    def volume(self, request: Request, query: EventVolumeParameters) -> Response:
        """Get event volume for specified filters and timeframe"""
        queryset: QuerySet[Event] = self.filter_queryset(self.get_queryset())
        delta = timedelta(days=query.validated_data.get("history_days", 7))
        if delta.total_seconds() > AGGR_MAX_AGE.total_seconds():
            delta = AGGR_MAX_AGE
        return Response(
            queryset.filter(created__gte=now() - delta)
            .annotate(
                # Six hour buckets starting at midnight UTC
                time=Func(
                    Value(timedelta(hours=6)),
                    "created",
                    Value(datetime(2000, 1, 1, tzinfo=UTC)),
                    function="DATE_BIN",
                    output_field=DjangoDateTimeField(),
                )
            )
            .values("time", "action")
            # COUNT(*) rather than counting the primary key, which the covering index on
            # created lacks; Postgres then counts from the index alone.
            .annotate(count=Count("*"))
            .order_by("time", "action")
        )

    @extend_schema(
        responses={200: EventStatsSerializer()},
        parameters=[EventStatsParameters],
        filters=True,
    )
    @action(detail=False, methods=["GET"], pagination_class=None)
    @validate(EventStatsParameters, "query")
    def stats(self, request: Request, query: EventStatsParameters) -> Response:
        """Get event stats for specified filters and count steps"""
        _now = now()
        aggrs = {
            "unique_users": Count("user__pk", distinct=True),
        }
        largest_delta = 0
        for step in query.validated_data.get("count_steps"):
            delta = timedelta_from_string(step)
            if delta.total_seconds() > AGGR_MAX_AGE.total_seconds():
                delta = AGGR_MAX_AGE
            largest_delta = max(largest_delta, delta.total_seconds())
            aggrs[slugify(step).replace("-", "_")] = Count(
                "event_uuid", filter=Q(created__gte=_now - delta)
            )
        data = (
            self.filter_queryset(self.get_queryset())
            .filter(created__gte=now() - timedelta(days=60))
            .aggregate(**aggrs)
        )
        return Response(
            {
                "unique_users": data.pop("unique_users"),
                "count_step": data,
            }
        )

    @extend_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def actions(self, request: Request) -> Response:
        """Get all actions"""
        data = []
        for value, name in EventAction.choices:
            data.append({"name": name, "description": "", "component": value, "model_name": ""})
        return Response(TypeCreateSerializer(data, many=True).data)
