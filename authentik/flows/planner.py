"""Flows Planner"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.http import HttpRequest
from sentry_sdk.hub import Hub
from sentry_sdk.tracing import Span
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.events.models import cleanse_dict
from authentik.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from authentik.flows.markers import ReevaluateMarker, StageMarker
from authentik.flows.models import Flow, FlowStageBinding, Stage
from authentik.policies.engine import PolicyEngine

LOGGER = get_logger()

PLAN_CONTEXT_PENDING_USER = "pending_user"
PLAN_CONTEXT_SSO = "is_sso"
PLAN_CONTEXT_REDIRECT = "redirect"
PLAN_CONTEXT_APPLICATION = "application"


def cache_key(flow: Flow, user: Optional[User] = None) -> str:
    """Generate Cache key for flow"""
    prefix = f"flow_{flow.pk}"
    if user:
        prefix += f"#{user.pk}"
    return prefix


@dataclass
class FlowPlan:
    """This data-class is the output of a FlowPlanner. It holds a flat list
    of all Stages that should be run."""

    flow_pk: str

    stages: List[Stage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    markers: List[StageMarker] = field(default_factory=list)

    def append(self, stage: Stage, marker: Optional[StageMarker] = None):
        """Append `stage` to all stages, optionall with stage marker"""
        self.stages.append(stage)
        self.markers.append(marker or StageMarker())

    def next(self, http_request: Optional[HttpRequest]) -> Optional[Stage]:
        """Return next pending stage from the bottom of the list"""
        if not self.has_stages:
            return None
        stage = self.stages[0]
        marker = self.markers[0]

        if marker.__class__ is not StageMarker:
            LOGGER.debug("f(plan_inst): stage has marker", stage=stage, marker=marker)
        marked_stage = marker.process(self, stage, http_request)
        if not marked_stage:
            LOGGER.debug("f(plan_inst): marker returned none, next stage", stage=stage)
            self.stages.remove(stage)
            self.markers.remove(marker)
            if not self.has_stages:
                return None
            # pylint: disable=not-callable
            return self.next(http_request)
        return marked_stage

    def pop(self):
        """Pop next pending stage from bottom of list"""
        self.markers.pop(0)
        self.stages.pop(0)

    @property
    def has_stages(self) -> bool:
        """Check if there are any stages left in this plan"""
        return len(self.markers) + len(self.stages) > 0


class FlowPlanner:
    """Execute all policies to plan out a flat list of all Stages
    that should be applied."""

    use_cache: bool
    allow_empty_flows: bool

    flow: Flow

    def __init__(self, flow: Flow):
        self.use_cache = True
        self.allow_empty_flows = False
        self.flow = flow

    def plan(
        self, request: HttpRequest, default_context: Optional[Dict[str, Any]] = None
    ) -> FlowPlan:
        """Check each of the flows' policies, check policies for each stage with PolicyBinding
        and return ordered list"""
        with Hub.current.start_span(op="flow.planner.plan") as span:
            span: Span
            span.set_data("flow", self.flow)
            span.set_data("request", request)

            LOGGER.debug("f(plan): Starting planning process", flow=self.flow)
            # Bit of a workaround here, if there is a pending user set in the default context
            # we use that user for our cache key
            # to make sure they don't get the generic response
            if default_context and PLAN_CONTEXT_PENDING_USER in default_context:
                user = default_context[PLAN_CONTEXT_PENDING_USER]
            else:
                user = request.user
            # First off, check the flow's direct policy bindings
            # to make sure the user even has access to the flow
            engine = PolicyEngine(self.flow, user, request)
            if default_context:
                span.set_data("default_context", cleanse_dict(default_context))
                engine.request.context = default_context
            engine.build()
            result = engine.result
            if not result.passing:
                raise FlowNonApplicableException(result.messages)
            # User is passing so far, check if we have a cached plan
            cached_plan_key = cache_key(self.flow, user)
            cached_plan = cache.get(cached_plan_key, None)
            if cached_plan and self.use_cache:
                LOGGER.debug(
                    "f(plan): Taking plan from cache",
                    flow=self.flow,
                    key=cached_plan_key,
                )
                # Reset the context as this isn't factored into caching
                cached_plan.context = default_context or {}
                return cached_plan
            LOGGER.debug("f(plan): building plan", flow=self.flow)
            plan = self._build_plan(user, request, default_context)
            cache.set(cache_key(self.flow, user), plan)
            if not plan.stages and not self.allow_empty_flows:
                raise EmptyFlowException()
            return plan

    def _build_plan(
        self,
        user: User,
        request: HttpRequest,
        default_context: Optional[Dict[str, Any]],
    ) -> FlowPlan:
        """Build flow plan by checking each stage in their respective
        order and checking the applied policies"""
        with Hub.current.start_span(op="flow.planner.build_plan") as span:
            span: Span
            span.set_data("flow", self.flow)
            span.set_data("user", user)
            span.set_data("request", request)

            plan = FlowPlan(flow_pk=self.flow.pk.hex)
            if default_context:
                plan.context = default_context
            # Check Flow policies
            for binding in FlowStageBinding.objects.filter(
                target__pk=self.flow.pk
            ).order_by("order"):
                binding: FlowStageBinding
                stage = binding.stage
                marker = StageMarker()
                if binding.evaluate_on_plan:
                    LOGGER.debug(
                        "f(plan): evaluating on plan",
                        stage=binding.stage,
                        flow=self.flow,
                    )
                    engine = PolicyEngine(binding, user, request)
                    engine.request.context = plan.context
                    engine.build()
                    if engine.passing:
                        LOGGER.debug(
                            "f(plan): Stage passing",
                            stage=binding.stage,
                            flow=self.flow,
                        )
                    else:
                        stage = None
                else:
                    LOGGER.debug(
                        "f(plan): not evaluating on plan",
                        stage=binding.stage,
                        flow=self.flow,
                    )
                if binding.re_evaluate_policies and stage:
                    LOGGER.debug(
                        "f(plan): Stage has re-evaluate marker",
                        stage=binding.stage,
                        flow=self.flow,
                    )
                    marker = ReevaluateMarker(binding=binding, user=user)
                if stage:
                    plan.append(stage, marker)
        LOGGER.debug(
            "f(plan): Finished building",
            flow=self.flow,
        )
        return plan
