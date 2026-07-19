from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_field
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, ChoiceField, SerializerMethodField
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.api.validation import validate
from authentik.brands.models import Brand
from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import (
    JSONDictField,
    LinkSerializer,
    ModelSerializer,
    PassiveSerializer,
)
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.requests.api.apps import RequestableTargetSerializer, user_can_request
from authentik.enterprise.requests.models import (
    GrantRequest,
    RequestRule,
    RequestStatus,
)
from authentik.enterprise.requests.stage import (
    PLAN_CONTEXT_GRANT_REQUESTED_PBMS,
    GrantRequestFinalStageView,
)
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from authentik.policies.api.bindings import PolicyBindingModelForeignKey
from authentik.policies.models import PolicyBindingModel, RequestableModel


class GrantRequestSerializer(EnterpriseRequiredMixin, ModelSerializer):

    created_by = PartialUserSerializer(read_only=True)
    revoked_by = PartialUserSerializer(read_only=True)
    is_active = BooleanField(read_only=True)

    target_objs = SerializerMethodField()

    @extend_schema_field(RequestableTargetSerializer(many=True))
    def get_target_objs(self, inst: GrantRequest) -> list[RequestableTargetSerializer]:
        return RequestableTargetSerializer(inst.targets.all().select_subclasses(), many=True).data

    class Meta:
        model = GrantRequest
        fields = [
            "created",
            "created_by",
            "requester_data",
            "fulfiller_data",
            "revoked_by",
            "is_active",
            "expires",
            "status",
            "targets",
            "target_objs",
            "uuid",
        ]
        extra_kwargs = {
            "status": {"read_only": True},
        }


class GrantRequestViewSet(RetrieveModelMixin, DestroyModelMixin, ListModelMixin, GenericViewSet):

    # All requests are visible to users even if they're expired
    queryset = GrantRequest.objects.including_expired()
    serializer_class = GrantRequestSerializer

    class GrantRequestCreateSerializer(PassiveSerializer):

        pbms = PolicyBindingModelForeignKey(
            queryset=PolicyBindingModel.objects.select_subclasses(), many=True
        )

        def validate_pbms(self, pbms: list[PolicyBindingModel]) -> list[PolicyBindingModel]:
            request = self.context["request"]
            for pbm in pbms:
                if not isinstance(pbm, RequestableModel):
                    raise ValidationError(f"'{pbm}' is not requestable")
                if not user_can_request(pbm, request.user, request):
                    raise ValidationError(f"Cannot request access to '{pbm.requestable_label}'")
            return pbms

    class GrantRequestFulfillSerializer(PassiveSerializer):

        data = JSONDictField()
        status = ChoiceField(choices=RequestStatus.choices)

    def _assert_reviewer(self, request: Request, grant: GrantRequest):
        rules = RequestRule.objects.filter(targets__in=grant.targets.all()).distinct()
        for rule in rules:
            if rule.reviewers.filter(pk=request.user.pk).exists():
                continue
            if rule.reviewer_groups.filter(users=request.user).exists():
                continue
            raise ValidationError("User does not have permissions to act on this object")

    @extend_schema(request=GrantRequestCreateSerializer, responses={200: LinkSerializer})
    @validate(GrantRequestCreateSerializer)
    def create(self, request: Request, body: GrantRequestCreateSerializer) -> Response:
        brand: Brand = request.brand
        # TODO: this flow should only be used as fallback, if all rules that granted the user
        # permissions to request each respective PBM share a request flow, use that flow,
        # otherwise just fallback to brand
        flow = brand.flow_request
        if not flow:
            raise Http404
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        plan = planner.plan(
            request,
            {
                PLAN_CONTEXT_GRANT_REQUESTED_PBMS: body.validated_data["pbms"],
                PLAN_CONTEXT_PENDING_USER: request.user,
            },
        )
        plan.append_stage(in_memory_stage(GrantRequestFinalStageView))
        return Response({"link": plan.to_redirect(request, flow).url})

    @extend_schema(
        request=GrantRequestFulfillSerializer,
        responses={
            204: OpenApiResponse(description="Request fulfilled"),
        },
    )
    @action(["PATCH"], detail=True)
    @validate(GrantRequestFulfillSerializer)
    def fulfill(self, request: Request, body: GrantRequestFulfillSerializer, *args, **kwargs):
        grant: GrantRequest = self.get_object()
        self._assert_reviewer(request, grant)
        grant.record_approval(
            request.user,
            body.validated_data.get("status"),
            data=body.validated_data.get("data"),
        )
        return Response(status=204)

    @extend_schema(
        request=None,
        responses={
            204: OpenApiResponse(description="Grant revoked"),
        },
    )
    @action(["POST"], detail=True)
    def revoke(self, request: Request, *args, **kwargs):
        """Immediately end an active grant. Available to the same reviewers who could
        approve it in the first place."""
        grant: GrantRequest = self.get_object()
        self._assert_reviewer(request, grant)
        grant.revoke(request.user)
        return Response(status=204)
