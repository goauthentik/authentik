"""Stage Markers"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.contrib.messages import INFO, add_message
from django.http.request import HttpRequest
from structlog.stdlib import get_logger

from authentik.events.models import Event, EventAction
from authentik.flows.models import FlowStageBinding
from authentik.policies.engine import PolicyEngine
from authentik.policies.models import PolicyBinding

if TYPE_CHECKING:
    from authentik.flows.planner import FlowPlan

LOGGER = get_logger()


@dataclass
class StageMarker:
    """Base stage marker class, no extra attributes, and has no special handler."""

    def process(
        self,
        plan: FlowPlan,
        binding: FlowStageBinding,
        http_request: HttpRequest,
    ) -> FlowStageBinding | None:
        """Process callback for this marker. This should be overridden by sub-classes.
        If a stage should be removed, return None."""
        return binding


@dataclass(slots=True)
class ReevaluateMarker(StageMarker):
    """Reevaluate Marker, forces stage's policies to be evaluated again."""

    binding: PolicyBinding

    def process(
        self,
        plan: FlowPlan,
        binding: FlowStageBinding,
        http_request: HttpRequest,
    ) -> FlowStageBinding | None:
        """Re-evaluate policies bound to stage, and if they fail, remove from plan"""
        from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER

        LOGGER.debug(
            "f(plan_inst): running re-evaluation",
            marker="ReevaluateMarker",
            binding=binding,
            policy_binding=self.binding,
        )
        user = plan.context.get(PLAN_CONTEXT_PENDING_USER, http_request.user)
        engine = PolicyEngine(self.binding, user)
        engine.use_cache = False
        engine.request.set_http_request(http_request)
        engine.request.context["flow_plan"] = plan
        engine.request.context.update(plan.context)
        engine.build()
        result = engine.result
        for message in result.messages:
            add_message(http_request, INFO, message)
        if result.passing:
            return binding
        LOGGER.warning(
            "f(plan_inst): binding failed re-evaluation",
            marker="ReevaluateMarker",
            binding=binding,
            messages=result.messages,
        )

        from authentik.stages.user_login.models import UserLoginStage

        if isinstance(binding.stage, UserLoginStage):
            Event.new(
                EventAction.LOGIN_BLOCKED,
                message="; ".join(str(message) for message in result.messages)
                or "Login blocked by policy.",
                reasons=sorted(result.reasons),
                subject=user if user.is_authenticated else None,
            ).from_http(http_request, user)
        return None
