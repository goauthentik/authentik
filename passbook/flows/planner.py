"""Flows Planner"""
from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, List, Optional, Tuple

from django.core.cache import cache
from django.http import HttpRequest
from structlog import get_logger

from passbook.core.models import User
from passbook.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from passbook.flows.models import Flow, Stage
from passbook.policies.engine import PolicyEngine

LOGGER = get_logger()

PLAN_CONTEXT_PENDING_USER = "pending_user"
PLAN_CONTEXT_SSO = "is_sso"


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

    def next(self) -> Stage:
        """Return next pending stage from the bottom of the list"""
        return self.stages[0]


class FlowPlanner:
    """Execute all policies to plan out a flat list of all Stages
    that should be applied."""

    use_cache: bool
    flow: Flow

    def __init__(self, flow: Flow):
        self.use_cache = True
        self.flow = flow

    def _check_flow_root_policies(self, request: HttpRequest) -> Tuple[bool, List[str]]:
        engine = PolicyEngine(self.flow.policies.all(), request.user, request)
        engine.build()
        return engine.result

    def plan(self, request: HttpRequest) -> FlowPlan:
        """Check each of the flows' policies, check policies for each stage with PolicyBinding
        and return ordered list"""
        LOGGER.debug("f(plan): Starting planning process", flow=self.flow)
        # First off, check the flow's direct policy bindings
        # to make sure the user even has access to the flow
        root_passing, root_passing_messages = self._check_flow_root_policies(request)
        if not root_passing:
            raise FlowNonApplicableException(root_passing_messages)
        cached_plan = cache.get(cache_key(self.flow, request.user), None)
        if cached_plan and self.use_cache:
            LOGGER.debug("f(plan): Taking plan from cache", flow=self.flow)
            return cached_plan
        start_time = time()
        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        # Check Flow policies
        for stage in (
            self.flow.stages.order_by("flowstagebinding__order")
            .select_subclasses()
            .select_related()
        ):
            binding = stage.flowstagebinding_set.get(flow__pk=self.flow.pk)
            engine = PolicyEngine(binding.policies.all(), request.user, request)
            engine.build()
            passing, _ = engine.result
            if passing:
                LOGGER.debug("f(plan): Stage passing", stage=stage, flow=self.flow)
                plan.stages.append(stage)
        end_time = time()
        LOGGER.debug(
            "f(plan): Finished planning",
            flow=self.flow,
            duration_s=end_time - start_time,
        )
        cache.set(cache_key(self.flow, request.user), plan)
        if not plan.stages:
            raise EmptyFlowException()
        return plan
