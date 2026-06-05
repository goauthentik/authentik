from drf_spectacular.utils import extend_schema
from rest_framework.fields import ListField
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
from authentik.core.api.utils import LinkSerializer, ModelSerializer, PassiveSerializer
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from authentik.pam.models import GrantRequest
from authentik.pam.stage import PLAN_CONTEXT_GRANT_REQUESTED_PBMS, GrantRequestFinalStageView
from authentik.policies.models import PolicyBindingModel


class GrantRequestSerializer(ModelSerializer):

    class Meta:
        model = GrantRequest
        fields = "__all__"


class GrantRequestViewSet(RetrieveModelMixin, DestroyModelMixin, ListModelMixin, GenericViewSet):

    queryset = GrantRequest.objects.all()
    serializer_class = GrantRequestSerializer

    class GrantRequestCreateSerializer(PassiveSerializer):
        pbms = ListField(child=PrimaryKeyRelatedField(queryset=PolicyBindingModel.objects.all()))

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
        return Response({"link": plan.to_redirect(request, flow)})
