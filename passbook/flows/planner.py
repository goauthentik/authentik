"""Flows Planner"""
from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, List, Tuple

from django.http import HttpRequest
from structlog import get_logger

from passbook.flows.exceptions import FlowNonApplicableError
from passbook.flows.models import Flow, Stage
from passbook.policies.engine import PolicyEngine

LOGGER = get_logger()

PLAN_CONTEXT_PENDING_USER = "pending_user"
PLAN_CONTEXT_SSO = "is_sso"


@dataclass
class FlowPlan:
    """This data-class is the output of a FlowPlanner. It holds a flat list
    of all Stages that should be run."""

    stages: List[Stage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def next(self) -> Stage:
        """Return next pending stage from the bottom of the list"""
        stage_cls = self.stages.pop(0)
        return stage_cls


class FlowPlanner:
    """Execute all policies to plan out a flat list of all Stages
    that should be applied."""

    flow: Flow

    def __init__(self, flow: Flow):
        self.flow = flow

    def _check_flow_root_policies(self, request: HttpRequest) -> Tuple[bool, List[str]]:
        engine = PolicyEngine(self.flow.policies.all(), request.user, request)
        engine.build()
        return engine.result

    def plan(self, request: HttpRequest) -> FlowPlan:
        """Check each of the flows' policies, check policies for each stage with PolicyBinding
        and return ordered list"""
        LOGGER.debug("Starting planning process", flow=self.flow)
        start_time = time()
        plan = FlowPlan()
        # First off, check the flow's direct policy bindings
        # to make sure the user even has access to the flow
        root_passing, root_passing_messages = self._check_flow_root_policies(request)
        if not root_passing:
            raise FlowNonApplicableError(root_passing_messages)
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
                LOGGER.debug("Stage passing", stage=stage)
                plan.stages.append(stage)
        end_time = time()
        LOGGER.debug(
            "Finished planning", flow=self.flow, duration_s=end_time - start_time
        )
        return plan
