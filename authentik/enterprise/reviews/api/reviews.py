from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import Q, F
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField, DateField, BooleanField, IntegerField
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import CreateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.reviews.api.attestations import AttestationSerializer
from authentik.enterprise.reviews.utils import parse_content_type, \
    ContentTypeField, ReviewerGroupSerializer, ReviewerUserSerializer, \
    admin_link_for_model
from authentik.enterprise.reviews.models import Review, ReviewState


class ReviewSerializer(EnterpriseRequiredMixin, ModelSerializer):
    content_type = ContentTypeField()
    object_verbose = SerializerMethodField()
    object_admin_url = SerializerMethodField(read_only=True)
    grace_period_end = SerializerMethodField(read_only=True)
    attestations = AttestationSerializer(many=True, read_only=True, source="attestation_set.all")
    user_can_attest = SerializerMethodField(read_only=True)

    reviewer_groups = ReviewerGroupSerializer(many=True, read_only=True,
                                              source="rule.reviewer_groups")
    min_reviewers = IntegerField(read_only=True, source="rule.min_reviewers")
    reviewers = ReviewerUserSerializer(many=True, read_only=True, source="rule.reviewers")

    next_review_date = SerializerMethodField(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "content_type", "object_id", "object_verbose", "object_admin_url", "state",
                  "opened_on", "grace_period_end", "next_review_date", "attestations",
                  "user_can_attest", "reviewer_groups", "min_reviewers", "reviewers"]
        read_only_fields = fields
        # read_only_fields = ["id", "opened_on", "object_verbose", "object_admin_url",
        #                     "grace_period_end", "next_review_date", "attestations",
        #                     "user_can_attest", "reviewer_groups", "min_reviewers", "reviewers"]

    def get_object_verbose(self, review: Review) -> str:
        return str(review.object)

    def get_object_admin_url(self, review: Review) -> str:
        return admin_link_for_model(review.object)

    @extend_schema_field(DateField())
    def get_grace_period_end(self, review: Review):
        return review.opened_on + timedelta(days=review.rule.grace_period_days)

    @extend_schema_field(DateField())
    def get_next_review_date(self, review: Review):
        return review.opened_on + relativedelta(months=review.rule.interval_months)

    @extend_schema_field(BooleanField())
    def get_user_can_attest(self, review: Review):
        return review.user_can_attest(self.context["request"].user)


class ReviewViewSet(EnterpriseRequiredMixin, CreateModelMixin, GenericViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    ordering_fields = ["state", "content_type__model", "opened_on", "grace_period_end"]

    @action(
        detail=False,
        methods=["get"],
        url_path=r"latest/(?P<content_type>[^/]+)/(?P<object_id>[^/]+)",
    )
    def latest_review(self, request: Request, content_type: str, object_id: str) -> Response:
        ct = parse_content_type(content_type)
        obj = get_object_or_404(
            self.get_queryset(),
            content_type__app_label=ct["app_label"],
            content_type__model=ct["model"],
            object_id=object_id,
        )
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @extend_schema(operation_id="reviews_reviews_list_open",
                   responses={200: ReviewSerializer(many=True)}, )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"open",
    )
    def open_reviews(self, request: Request):
        reviews = self.get_queryset().filter(
            Q(state=ReviewState.PENDING) | Q(state=ReviewState.OVERDUE))
        reviews = self.filter_queryset(reviews)
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
