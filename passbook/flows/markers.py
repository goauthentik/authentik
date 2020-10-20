"""Stage Markers"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from django.http.request import HttpRequest
from structlog import get_logger

from passbook.core.models import User
from passbook.flows.models import Stage
from passbook.policies.engine import PolicyEngine
from passbook.policies.models import PolicyBinding

if TYPE_CHECKING:
    from passbook.flows.planner import FlowPlan

LOGGER = get_logger()


@dataclass
class StageMarker:
    """Base stage marker class, no extra attributes, and has no special handler."""

    # pylint: disable=unused-argument
    def process(
        self, plan: "FlowPlan", stage: Stage, http_request: Optional[HttpRequest]
    ) -> Optional[Stage]:
        """Process callback for this marker. This should be overridden by sub-classes.
        If a stage should be removed, return None."""
        return stage


@dataclass
class ReevaluateMarker(StageMarker):
    """Reevaluate Marker, forces stage's policies to be evaluated again."""

    binding: PolicyBinding
    user: User

    def process(
        self, plan: "FlowPlan", stage: Stage, http_request: Optional[HttpRequest]
    ) -> Optional[Stage]:
        """Re-evaluate policies bound to stage, and if they fail, remove from plan"""
        engine = PolicyEngine(self.binding, self.user)
        engine.use_cache = False
        if http_request:
            engine.request.http_request = http_request
        engine.request.context = plan.context
        engine.build()
        result = engine.result
        if result.passing:
            return stage
        LOGGER.warning(
            "f(plan_inst)[re-eval marker]: stage failed re-evaluation",
            stage=stage,
            messages=result.messages,
        )
        return None
