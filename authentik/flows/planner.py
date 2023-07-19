"""Flows Planner"""
from dataclasses import dataclass, field
from typing import Any, Optional

from django.core.cache import cache
from django.http import HttpRequest
from sentry_sdk.hub import Hub
from sentry_sdk.tracing import Span
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import User
from authentik.events.models import cleanse_dict
from authentik.flows.apps import HIST_FLOWS_PLAN_TIME
from authentik.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from authentik.flows.markers import ReevaluateMarker, StageMarker
from authentik.flows.models import (
    Flow,
    FlowAuthenticationRequirement,
    FlowDesignation,
    FlowStageBinding,
    Stage,
    in_memory_stage,
)
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
CACHE_TIMEOUT = int(CONFIG.get("redis.cache_timeout_flows"))
CACHE_PREFIX = "goauthentik.io/flows/planner/"


def cache_key(flow: Flow, user: Optional[User] = None) -> str:
    """Generate Cache key for flow"""
    prefix = CACHE_PREFIX + str(flow.pk)
    if user:
        prefix += f"#{user.pk}"
    return prefix


@dataclass(slots=True)
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

    def redirect(self, destination: str):
        """Insert a redirect stage as next stage"""
        from authentik.flows.stage import RedirectStage

        self.insert_stage(in_memory_stage(RedirectStage, destination=destination))

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

    def _check_authentication(self, request: HttpRequest):
        """Check the flow's authentication level is matched by `request`"""
        if (
            self.flow.authentication == FlowAuthenticationRequirement.REQUIRE_AUTHENTICATED
            and not request.user.is_authenticated
        ):
            raise FlowNonApplicableException()
        if (
            self.flow.authentication == FlowAuthenticationRequirement.REQUIRE_UNAUTHENTICATED
            and request.user.is_authenticated
        ):
            raise FlowNonApplicableException()
        if (
            self.flow.authentication == FlowAuthenticationRequirement.REQUIRE_SUPERUSER
            and not request.user.is_superuser
        ):
            raise FlowNonApplicableException()

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
                # We only need to check the flow authentication if it's planned without a user
                # in the context, as a user in the context can only be set via the explicit code API
                # or if a flow is restarted due to `invalid_response_action` being set to
                # `restart_with_context`, which can only happen if the user was already authorized
                # to use the flow
                self._check_authentication(request)
            # First off, check the flow's direct policy bindings
            # to make sure the user even has access to the flow
            engine = PolicyEngine(self.flow, user, request)
            engine.use_cache = self.use_cache
            if default_context:
                span.set_data("default_context", cleanse_dict(default_context))
                engine.request.context.update(default_context)
            engine.build()
            result = engine.result
            if not result.passing:
                exc = FlowNonApplicableException()
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
        with (
            Hub.current.start_span(
                op="authentik.flow.planner.build_plan",
                description=self.flow.slug,
            ) as span,
            HIST_FLOWS_PLAN_TIME.labels(flow_slug=self.flow.slug).time(),
        ):
            span: Span
            span.set_data("flow", self.flow)
            span.set_data("user", user)
            span.set_data("request", request)

            plan = FlowPlan(flow_pk=self.flow.pk.hex)
            if default_context:
                plan.context = default_context
            # Check Flow policies
            bindings = list(
                FlowStageBinding.objects.filter(target__pk=self.flow.pk).order_by("order")
            )
            stages = Stage.objects.filter(flowstagebinding__in=[binding.pk for binding in bindings])
            for binding in bindings:
                binding: FlowStageBinding
                stage = [stage for stage in stages if stage.pk == binding.stage_id][0]
                marker = StageMarker()
                if binding.evaluate_on_plan:
                    self._logger.debug(
                        "f(plan): evaluating on plan",
                        stage=stage,
                    )
                    engine = PolicyEngine(binding, user, request)
                    engine.use_cache = self.use_cache
                    engine.request.context["flow_plan"] = plan
                    engine.request.context.update(plan.context)
                    engine.build()
                    if engine.passing:
                        self._logger.debug(
                            "f(plan): stage passing",
                            stage=stage,
                        )
                    else:
                        stage = None
                else:
                    self._logger.debug(
                        "f(plan): not evaluating on plan",
                        stage=stage,
                    )
                if binding.re_evaluate_policies and stage:
                    self._logger.debug(
                        "f(plan): stage has re-evaluate marker",
                        stage=stage,
                    )
                    marker = ReevaluateMarker(binding=binding)
                if stage:
                    plan.append(binding, marker)
        self._logger.debug(
            "f(plan): finished building",
        )
        return plan
