"""Flows Planner"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from sentry_sdk import start_span
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
from authentik.lib.utils.urls import redirect_with_qs
from authentik.outposts.models import Outpost
from authentik.policies.engine import PolicyEngine
from authentik.root.middleware import ClientIPMiddleware

if TYPE_CHECKING:
    from authentik.flows.stage import StageView


LOGGER = get_logger()
PLAN_CONTEXT_PENDING_USER = "pending_user"
PLAN_CONTEXT_SSO = "is_sso"
PLAN_CONTEXT_REDIRECT = "redirect"
PLAN_CONTEXT_APPLICATION = "application"
PLAN_CONTEXT_SOURCE = "source"
PLAN_CONTEXT_OUTPOST = "outpost"
# Is set by the Flow Planner when a FlowToken was used, and the currently active flow plan
# was restored.
PLAN_CONTEXT_IS_RESTORED = "is_restored"
PLAN_CONTEXT_IS_REDIRECTED = "is_redirected"
PLAN_CONTEXT_REDIRECT_STAGE_TARGET = "redirect_stage_target"
CACHE_TIMEOUT = CONFIG.get_int("cache.timeout_flows")
CACHE_PREFIX = "goauthentik.io/flows/planner/"


def cache_key(flow: Flow, user: User | None = None) -> str:
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

    def append_stage(self, stage: Stage, marker: StageMarker | None = None):
        """Append `stage` to the end of the plan, optionally with stage marker"""
        return self.append(FlowStageBinding(stage=stage), marker)

    def append(self, binding: FlowStageBinding, marker: StageMarker | None = None):
        """Append `stage` to the end of the plan, optionally with stage marker"""
        self.bindings.append(binding)
        self.markers.append(marker or StageMarker())

    def insert_stage(self, stage: Stage, marker: StageMarker | None = None):
        """Insert stage into plan, as immediate next stage"""
        self.bindings.insert(1, FlowStageBinding(stage=stage, order=0))
        self.markers.insert(1, marker or StageMarker())

    def redirect(self, destination: str):
        """Insert a redirect stage as next stage"""
        from authentik.flows.stage import RedirectStage

        self.insert_stage(in_memory_stage(RedirectStage, destination=destination))

    def next(self, http_request: HttpRequest | None) -> FlowStageBinding | None:
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

            return self.next(http_request)
        return marked_stage

    def pop(self):
        """Pop next pending stage from bottom of list"""
        if not self.markers and not self.bindings:
            return
        self.markers.pop(0)
        self.bindings.pop(0)

    @property
    def has_stages(self) -> bool:
        """Check if there are any stages left in this plan"""
        return len(self.markers) + len(self.bindings) > 0

    def requires_flow_executor(
        self,
        allowed_silent_types: list["StageView"] | None = None,
    ):
        # Check if we actually need to show the Flow executor, or if we can jump straight to the end
        found_unskippable = True
        if allowed_silent_types:
            LOGGER.debug("Checking if we can skip the flow executor...")
            # Policies applied to the flow have already been evaluated, so we're checking for stages
            # allow-listed or bindings that require a policy re-eval
            found_unskippable = False
            for binding, marker in zip(self.bindings, self.markers, strict=True):
                if binding.stage.view not in allowed_silent_types:
                    found_unskippable = True
                if marker and isinstance(marker, ReevaluateMarker):
                    found_unskippable = True
        LOGGER.debug("Required flow executor status", status=found_unskippable)
        return found_unskippable

    def to_redirect(
        self,
        request: HttpRequest,
        flow: Flow,
        allowed_silent_types: list["StageView"] | None = None,
    ) -> HttpResponse:
        """Redirect to the flow executor for this flow plan"""
        from authentik.flows.views.executor import (
            SESSION_KEY_PLAN,
            FlowExecutorView,
        )

        request.session[SESSION_KEY_PLAN] = self
        requires_flow_executor = self.requires_flow_executor(allowed_silent_types)

        if not requires_flow_executor:
            # No unskippable stages found, so we can directly return the response of the last stage
            final_stage: type[StageView] = self.bindings[-1].stage.view
            temp_exec = FlowExecutorView(flow=flow, request=request, plan=self)
            temp_exec.current_stage = self.bindings[-1].stage
            temp_exec.current_stage_view = final_stage
            temp_exec.setup(request, flow.slug)
            stage = final_stage(request=request, executor=temp_exec)
            response = stage.dispatch(request)
            # Ensure we clean the flow state we have in the session before we redirect away
            temp_exec.stage_ok()
            return response

        return redirect_with_qs(
            "authentik_core:if-flow",
            request.GET,
            flow_slug=flow.slug,
        )


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

    def _check_authentication(self, request: HttpRequest, context: dict[str, Any]):
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
        if (
            self.flow.authentication == FlowAuthenticationRequirement.REQUIRE_REDIRECT
            and context.get(PLAN_CONTEXT_IS_REDIRECTED) is None
        ):
            raise FlowNonApplicableException()
        outpost_user = ClientIPMiddleware.get_outpost_user(request)
        if self.flow.authentication == FlowAuthenticationRequirement.REQUIRE_OUTPOST:
            if not outpost_user:
                raise FlowNonApplicableException()
        if outpost_user:
            outpost = Outpost.objects.filter(
                # TODO: Since Outpost and user are not directly connected, we have to look up a user
                # like this. This should ideally by in authentik/outposts/models.py
                pk=outpost_user.username.replace("ak-outpost-", "")
            ).first()
            if outpost:
                return {
                    PLAN_CONTEXT_OUTPOST: {
                        "instance": outpost,
                    }
                }
        return {}

    def plan(self, request: HttpRequest, default_context: dict[str, Any] | None = None) -> FlowPlan:
        """Check each of the flows' policies, check policies for each stage with PolicyBinding
        and return ordered list"""
        with start_span(op="authentik.flow.planner.plan", name=self.flow.slug) as span:
            span: Span
            span.set_data("flow", self.flow)
            span.set_data("request", request)

            self._logger.debug(
                "f(plan): starting planning process",
            )
            context = default_context or {}
            # Bit of a workaround here, if there is a pending user set in the default context
            # we use that user for our cache key to make sure they don't get the generic response
            if context and PLAN_CONTEXT_PENDING_USER in context:
                user = context[PLAN_CONTEXT_PENDING_USER]
            else:
                user = request.user

            context.update(self._check_authentication(request, context))
            # First off, check the flow's direct policy bindings
            # to make sure the user even has access to the flow
            engine = PolicyEngine(self.flow, user, request)
            engine.use_cache = self.use_cache
            span.set_data("context", cleanse_dict(context))
            engine.request.context.update(context)
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
                    cached_plan.context = context
                    return cached_plan
            self._logger.debug(
                "f(plan): building plan",
            )
            plan = self._build_plan(user, request, context)
            if self.use_cache:
                cache.set(cache_key(self.flow, user), plan, CACHE_TIMEOUT)
            if not plan.bindings and not self.allow_empty_flows:
                raise EmptyFlowException()
            return plan

    def _build_plan(
        self,
        user: User,
        request: HttpRequest,
        default_context: dict[str, Any] | None,
    ) -> FlowPlan:
        """Build flow plan by checking each stage in their respective
        order and checking the applied policies"""
        with (
            start_span(
                op="authentik.flow.planner.build_plan",
                name=self.flow.slug,
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
