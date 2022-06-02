"""Flows Planner"""
from dataclasses import dataclass, field
from typing import Any, Optional

from django.core.cache import cache
from django.http import HttpRequest
from prometheus_client import Gauge, Histogram
from sentry_sdk.hub import Hub
from sentry_sdk.tracing import Span
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import User
from authentik.events.models import cleanse_dict
from authentik.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from authentik.flows.markers import ReevaluateMarker, StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding, Stage
from authentik.lib.config import CONFIG
from authentik.policies.engine import PolicyEngine

LOGGER = get_logger()
PLAN_CONTEXT_PENDING_USER = "pending_user"
PLAN_CONTEXT_SSO = "is_sso"
PLAN_CONTEXT_REDIRECT = "redirect"
PLAN_CONTEXT_APPLICATION = "application"
PLAN_CONTEXT_SOURCE = "source"
# Is set by the Flow Planner when a FlowToken was used, and the currently active flow plan
# was restored.
PLAN_CONTEXT_IS_RESTORED = "is_restored"
GAUGE_FLOWS_CACHED = Gauge(
    "authentik_flows_cached",
    "Cached flows",
)
HIST_FLOWS_PLAN_TIME = Histogram(
    "authentik_flows_plan_time",
    "Duration to build a plan for a flow",
    ["flow_slug"],
)
CACHE_TIMEOUT = int(CONFIG.y("redis.cache_timeout_flows"))


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

    bindings: list[FlowStageBinding] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    markers: list[StageMarker] = field(default_factory=list)

    def append_stage(self, stage: Stage, marker: Optional[StageMarker] = None):
        """Append `stage` to all stages, optionally with stage marker"""
        return self.append(FlowStageBinding(stage=stage), marker)

    def append(self, binding: FlowStageBinding, marker: Optional[StageMarker] = None):
        """Append `stage` to all stages, optionally with stage marker"""
        self.bindings.append(binding)
        self.markers.append(marker or StageMarker())

    def insert_stage(self, stage: Stage, marker: Optional[StageMarker] = None):
        """Insert stage into plan, as immediate next stage"""
        self.bindings.insert(1, FlowStageBinding(stage=stage, order=0))
        self.markers.insert(1, marker or StageMarker())

    def next(self, http_request: Optional[HttpRequest]) -> Optional[FlowStageBinding]:
        """Return next pending stage from the bottom of the list"""
        if not self.has_stages:
            return None
        binding = self.bindings[0]
        marker = self.markers[0]

        if marker.__class__ is not StageMarker:
            LOGGER.debug("f(plan_inst): stage has marker", binding=binding, marker=marker)
        marked_stage = marker.process(self, binding, http_request)
        if not marked_stage:
            LOGGER.debug("f(plan_inst): marker returned none, next stage", binding=binding)
            self.bindings.remove(binding)
            self.markers.remove(marker)
            if not self.has_stages:
                return None
            # pylint: disable=not-callable
            return self.next(http_request)
        return marked_stage

    def pop(self):
        """Pop next pending stage from bottom of list"""
        self.markers.pop(0)
        self.bindings.pop(0)

    @property
    def has_stages(self) -> bool:
        """Check if there are any stages left in this plan"""
        return len(self.markers) + len(self.bindings) > 0


class FlowPlanner:
    """Execute all policies to plan out a flat list of all Stages
    that should be applied."""

    use_cache: bool
    allow_empty_flows: bool

    flow: Flow

    _logger: BoundLogger

    def __init__(self, flow: Flow):
        self.use_cache = True
        self.allow_empty_flows = False
        self.flow = flow
        self._logger = get_logger().bind(flow_slug=flow.slug)

    def plan(
        self, request: HttpRequest, default_context: Optional[dict[str, Any]] = None
    ) -> FlowPlan:
        """Check each of the flows' policies, check policies for each stage with PolicyBinding
        and return ordered list"""
        with Hub.current.start_span(
            op="authentik.flow.planner.plan", description=self.flow.slug
        ) as span:
            span: Span
            span.set_data("flow", self.flow)
            span.set_data("request", request)

            self._logger.debug(
                "f(plan): starting planning process",
            )
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
                exc = FlowNonApplicableException(",".join(result.messages))
                exc.policy_result = result
                raise exc
            # User is passing so far, check if we have a cached plan
            cached_plan_key = cache_key(self.flow, user)
            cached_plan = cache.get(cached_plan_key, None)
            if self.flow.designation not in [FlowDesignation.STAGE_CONFIGURATION]:
                if cached_plan and self.use_cache:
                    self._logger.debug(
                        "f(plan): taking plan from cache",
                        key=cached_plan_key,
                    )
                    # Reset the context as this isn't factored into caching
                    cached_plan.context = default_context or {}
                    return cached_plan
            self._logger.debug(
                "f(plan): building plan",
            )
            plan = self._build_plan(user, request, default_context)
            cache.set(cache_key(self.flow, user), plan, CACHE_TIMEOUT)
            if not plan.bindings and not self.allow_empty_flows:
                raise EmptyFlowException()
            return plan

    def _build_plan(
        self,
        user: User,
        request: HttpRequest,
        default_context: Optional[dict[str, Any]],
    ) -> FlowPlan:
        """Build flow plan by checking each stage in their respective
        order and checking the applied policies"""
        with Hub.current.start_span(
            op="authentik.flow.planner.build_plan",
            description=self.flow.slug,
        ) as span, HIST_FLOWS_PLAN_TIME.labels(flow_slug=self.flow.slug).time():
            span: Span
            span.set_data("flow", self.flow)
            span.set_data("user", user)
            span.set_data("request", request)

            plan = FlowPlan(flow_pk=self.flow.pk.hex)
            if default_context:
                plan.context = default_context
            # Check Flow policies
            for binding in FlowStageBinding.objects.filter(target__pk=self.flow.pk).order_by(
                "order"
            ):
                binding: FlowStageBinding
                stage = binding.stage
                marker = StageMarker()
                if binding.evaluate_on_plan:
                    self._logger.debug(
                        "f(plan): evaluating on plan",
                        stage=binding.stage,
                    )
                    engine = PolicyEngine(binding, user, request)
                    engine.request.context = plan.context
                    engine.build()
                    if engine.passing:
                        self._logger.debug(
                            "f(plan): stage passing",
                            stage=binding.stage,
                        )
                    else:
                        stage = None
                else:
                    self._logger.debug(
                        "f(plan): not evaluating on plan",
                        stage=binding.stage,
                    )
                if binding.re_evaluate_policies and stage:
                    self._logger.debug(
                        "f(plan): stage has re-evaluate marker",
                        stage=binding.stage,
                    )
                    marker = ReevaluateMarker(binding=binding)
                if stage:
                    plan.append(binding, marker)
            HIST_FLOWS_PLAN_TIME.labels(flow_slug=self.flow.slug)
        self._logger.debug(
            "f(plan): finished building",
        )
        return plan
