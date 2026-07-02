from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ChoiceField
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.api.validation import validate
from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import (
    JSONDictField,
    LinkSerializer,
    ModelSerializer,
    PassiveSerializer,
)
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from authentik.pam.models import GrantRequest, PolicyBindingModelRequestRule, RequestStatus
from authentik.pam.stage import PLAN_CONTEXT_GRANT_REQUESTED_PBMS, GrantRequestFinalStageView
from authentik.policies.models import PolicyBindingModel


class GrantRequestSerializer(ModelSerializer):
    created_by = PartialUserSerializer(read_only=True)

    class Meta:
        model = GrantRequest
        fields = [
            "created",
            "created_by",
            "requester_data",
            "fulfiller_data",
            "expires",
            "status",
            "targets",
            "uuid",
        ]


class GrantRequestViewSet(RetrieveModelMixin, DestroyModelMixin, ListModelMixin, GenericViewSet):
    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestSerializer

    class GrantRequestCreateSerializer(PassiveSerializer):
        pbms = PrimaryKeyRelatedField(queryset=PolicyBindingModel.objects.all(), many=True)

    class GrantRequestFulfillSerializer(PassiveSerializer):
        data = JSONDictField()
        status = ChoiceField(choices=RequestStatus.choices)

    @extend_schema(request=GrantRequestCreateSerializer, responses={200: LinkSerializer})
    @validate(GrantRequestCreateSerializer)
    def create(self, request: Request, body: GrantRequestCreateSerializer) -> Response:
        # TODO: Select a flow somewhere
        flow = Flow.objects.get(slug="request-access")
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
        unauthorized_rules = (
            PolicyBindingModelRequestRule.objects.filter(pbm__in=grant.targets.all())
            .exclude(reviewers=request.user)
            .exclude(reviewer_groups__users=request.user)
        )
        if unauthorized_rules.exists():
            raise ValidationError("User does not have permissions to approve object")
        # TODO: Check if this user can fulfill this grant
        grant.fulfill(
            body.validated_data.get("status"), request.user, data=body.validated_data.get("data")
        )
        return Response(status=204)
