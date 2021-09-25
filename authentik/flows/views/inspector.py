"""Flow Inspector"""
from hashlib import sha256
from typing import Any

from django.conf import settings
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.fields import ListField, SerializerMethodField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.api.utils import PassiveSerializer
from authentik.events.utils import sanitize_dict
from authentik.flows.api.bindings import FlowStageBindingSerializer
from authentik.flows.models import Flow
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_HISTORY, SESSION_KEY_PLAN


class FlowInspectorPlanSerializer(PassiveSerializer):
    """Serializer for an active FlowPlan"""

    current_stage = SerializerMethodField()
    next_planned_stage = SerializerMethodField(required=False)
    plan_context = SerializerMethodField()
    session_id = SerializerMethodField()

    def get_current_stage(self, plan: FlowPlan) -> FlowStageBindingSerializer:
        """Get the current stage"""
        return FlowStageBindingSerializer(instance=plan.bindings[0]).data

    def get_next_planned_stage(self, plan: FlowPlan) -> FlowStageBindingSerializer:
        """Get the next planned stage"""
        if len(plan.bindings) < 1:
            return FlowStageBindingSerializer()
        return FlowStageBindingSerializer(instance=plan.bindings[1]).data

    def get_plan_context(self, plan: FlowPlan) -> dict[str, Any]:
        """Get the plan's context, sanitized"""
        return sanitize_dict(plan.context)

    # pylint: disable=unused-argument
    def get_session_id(self, plan: FlowPlan) -> str:
        """Get a unique session ID"""
        request: Request = self.context["request"]
        return sha256(
            f"{request._request.session.session_key}-{settings.SECRET_KEY}".encode("ascii")
        ).hexdigest()


class FlowInspectionSerializer(PassiveSerializer):
    """Serializer for inspect endpoint"""

    plans = ListField(child=FlowInspectorPlanSerializer())
    current_plan = FlowInspectorPlanSerializer()


@method_decorator(xframe_options_sameorigin, name="dispatch")
class FlowInspectorView(APIView):
    """Flow inspector API"""

    permission_classes = [IsAdminUser]

    flow: Flow
    _logger: BoundLogger

    def setup(self, request: HttpRequest, flow_slug: str):
        super().setup(request, flow_slug=flow_slug)
        self.flow = get_object_or_404(Flow.objects.select_related(), slug=flow_slug)
        self._logger = get_logger().bind(flow_slug=flow_slug)

    # pylint: disable=unused-argument, too-many-return-statements
    def dispatch(self, request: HttpRequest, flow_slug: str) -> HttpResponse:
        # Early check if there's an active Plan for the current session
        if SESSION_KEY_PLAN not in self.request.session:
            return HttpResponse(status=400)
        return super().dispatch(request, flow_slug=flow_slug)

    @extend_schema(
        responses={
            200: FlowInspectionSerializer(),
            400: OpenApiResponse(
                description="No flow plan in session."
            ),  # This error can be raised by the email stage
        },
        request=OpenApiTypes.NONE,
        operation_id="flows_inspector_get",
    )
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Get current flow state and record it"""
        current_plan: FlowPlan = request.session[SESSION_KEY_PLAN]
        plans = []
        for plan in request.session[SESSION_KEY_HISTORY]:
            plan_serializer = FlowInspectorPlanSerializer(
                instance=plan, context={"request": request}
            )
            plans.append(plan_serializer.data)
        current_serializer = FlowInspectorPlanSerializer(
            instance=current_plan, context={"request": request}
        )
        response = FlowInspectionSerializer(data={"plans": plans})
        response.is_valid()
        data = response.data
        data["current_plan"] = current_serializer.data
        return Response(data)
