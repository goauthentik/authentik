from datetime import datetime

from django.db.models import Exists, OuterRef, Q, Subquery
from django_filters.rest_framework import BooleanFilter, FilterSet
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.mixins import CreateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.lifecycle.api.reviews import ReviewSerializer
from authentik.enterprise.lifecycle.models import LifecycleIteration, LifecycleRule, ReviewState
from authentik.enterprise.lifecycle.utils import (
    ContentTypeField,
    ReviewerGroupSerializer,
    ReviewerUserSerializer,
    admin_link_for_model,
    parse_content_type,
    start_of_day,
)
from authentik.lib.utils.time import timedelta_from_string


class RelatedRuleSerializer(EnterpriseRequiredMixin, ModelSerializer):
    reviewer_groups = ReviewerGroupSerializer(many=True, read_only=True)
    min_reviewers = IntegerField(read_only=True)
    reviewers = ReviewerUserSerializer(many=True, read_only=True)

    class Meta:
        model = LifecycleRule
        fields = ["id", "name", "reviewer_groups", "min_reviewers", "reviewers"]


class LifecycleIterationSerializer(EnterpriseRequiredMixin, ModelSerializer):
    content_type = ContentTypeField()
    object_verbose = SerializerMethodField()
    rule = RelatedRuleSerializer(read_only=True)
    object_admin_url = SerializerMethodField(read_only=True)
    grace_period_end = SerializerMethodField(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True, source="review_set.all")
    user_can_review = SerializerMethodField(read_only=True)

    next_review_date = SerializerMethodField(read_only=True)

    class Meta:
        model = LifecycleIteration
        fields = [
            "id",
            "content_type",
            "object_id",
            "object_verbose",
            "object_admin_url",
            "state",
            "opened_on",
            "grace_period_end",
            "next_review_date",
            "reviews",
            "rule",
            "user_can_review",
        ]
        read_only_fields = fields

    def get_object_verbose(self, iteration: LifecycleIteration) -> str:
        return str(iteration.object)

    def get_object_admin_url(self, iteration: LifecycleIteration) -> str:
        return admin_link_for_model(iteration.object)

    def get_grace_period_end(self, iteration: LifecycleIteration) -> datetime:
        return start_of_day(
            iteration.opened_on + timedelta_from_string(iteration.rule.grace_period)
        )

    def get_next_review_date(self, iteration: LifecycleIteration) -> datetime:
        return start_of_day(iteration.opened_on + timedelta_from_string(iteration.rule.interval))

    def get_user_can_review(self, iteration: LifecycleIteration) -> bool:
        return iteration.user_can_review(self.context["request"].user)


class LifecycleIterationFilterSet(FilterSet):
    user_is_reviewer = BooleanFilter(field_name="user_is_reviewer", lookup_expr="exact")


class IterationViewSet(EnterpriseRequiredMixin, CreateModelMixin, GenericViewSet):
    queryset = LifecycleIteration.objects.all()
    serializer_class = LifecycleIterationSerializer
    ordering = ["-opened_on"]
    ordering_fields = [
        "state",
        "content_type__model",
        "rule__name",
        "opened_on",
        "grace_period_end",
    ]
    filterset_class = LifecycleIterationFilterSet

    def get_queryset(self):
        user = self.request.user
        return self.queryset.annotate(
            user_is_reviewer=Exists(
                LifecycleRule.objects.filter(
                    pk=OuterRef("rule_id"),
                ).filter(
                    Q(reviewers=user) | Q(reviewer_groups__in=user.groups.all().with_ancestors())
                )
            )
        )

    @extend_schema(
        operation_id="lifecycle_iterations_list_latest",
        responses={200: LifecycleIterationSerializer(many=True)},
    )
    @action(
        detail=False,
        pagination_class=None,
        methods=["get"],
        url_path=r"latest/(?P<content_type>[^/]+)/(?P<object_id>[^/]+)",
    )
    def latest_iterations(self, request: Request, content_type: str, object_id: str) -> Response:
        ct = parse_content_type(content_type)
        latest_ids_subquery = (
            LifecycleIteration.objects.filter(
                rule=OuterRef("rule"),
                content_type__app_label=ct["app_label"],
                content_type__model=ct["model"],
                object_id=object_id,
            )
            .order_by("-opened_on")
            .values("id")[:1]
        )
        latest_per_rule = LifecycleIteration.objects.filter(
            content_type__app_label=ct["app_label"],
            content_type__model=ct["model"],
            object_id=object_id,
        ).filter(id=Subquery(latest_ids_subquery))
        serializer = self.get_serializer(latest_per_rule, many=True)
        return Response(serializer.data)

    @extend_schema(
        operation_id="lifecycle_iterations_list_open",
        responses={200: LifecycleIterationSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"open",
    )
    def open_iterations(self, request: Request):
        iterations = self.get_queryset().filter(
            Q(state=ReviewState.PENDING) | Q(state=ReviewState.OVERDUE)
        )
        iterations = self.filter_queryset(iterations)
        page = self.paginate_queryset(iterations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(iterations, many=True)
        return Response(serializer.data)
