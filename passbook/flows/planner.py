"""Flows Planner"""
from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.http import HttpRequest
from structlog import get_logger

from passbook.core.models import User
from passbook.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from passbook.flows.models import Flow, Stage
from passbook.policies.engine import PolicyEngine
from passbook.policies.types import PolicyResult

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

    def _check_flow_root_policies(self, request: HttpRequest) -> PolicyResult:
        engine = PolicyEngine(self.flow, request.user, request)
        engine.build()
        return engine.result

    def plan(
        self, request: HttpRequest, default_context: Optional[Dict[str, Any]] = None
    ) -> FlowPlan:
        """Check each of the flows' policies, check policies for each stage with PolicyBinding
        and return ordered list"""
        LOGGER.debug("f(plan): Starting planning process", flow=self.flow)
        # First off, check the flow's direct policy bindings
        # to make sure the user even has access to the flow
        root_result = self._check_flow_root_policies(request)
        if not root_result.passing:
            raise FlowNonApplicableException(*root_result.messages)
        # Bit of a workaround here, if there is a pending user set in the default context
        # we use that user for our cache key
        # to make sure they don't get the generic response
        if default_context and PLAN_CONTEXT_PENDING_USER in default_context:
            user = default_context[PLAN_CONTEXT_PENDING_USER]
        else:
            user = request.user
        cached_plan_key = cache_key(self.flow, user)
        cached_plan = cache.get(cached_plan_key, None)
        if cached_plan and self.use_cache:
            LOGGER.debug(
                "f(plan): Taking plan from cache", flow=self.flow, key=cached_plan_key
            )
            LOGGER.debug(cached_plan)
            return cached_plan
        plan = self._build_plan(user, request, default_context)
        cache.set(cache_key(self.flow, user), plan)
        if not plan.stages:
            raise EmptyFlowException()
        return plan

    def _build_plan(
        self,
        user: User,
        request: HttpRequest,
        default_context: Optional[Dict[str, Any]],
    ) -> FlowPlan:
        """Actually build flow plan"""
        start_time = time()
        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        if default_context:
            plan.context = default_context
        # Check Flow policies
        for stage in (
            self.flow.stages.order_by("flowstagebinding__order")
            .select_subclasses()
            .select_related()
        ):
            binding = stage.flowstagebinding_set.get(flow__pk=self.flow.pk)
            engine = PolicyEngine(binding, user, request)
            engine.request.context = plan.context
            engine.build()
            if engine.passing:
                LOGGER.debug("f(plan): Stage passing", stage=stage, flow=self.flow)
                plan.stages.append(stage)
        end_time = time()
        LOGGER.debug(
            "f(plan): Finished building",
            flow=self.flow,
            duration_s=end_time - start_time,
        )
        return plan
