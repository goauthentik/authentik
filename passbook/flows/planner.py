"""Flows Planner"""
from dataclasses import dataclass, field
from time import time
from typing import List, Tuple

from django.http import HttpRequest
from structlog import get_logger

from passbook.flows.exceptions import FlowNonApplicableError
from passbook.flows.models import Factor, Flow
from passbook.policies.engine import PolicyEngine

LOGGER = get_logger()


@dataclass
class FlowPlan:
    """This data-class is the output of a FlowPlanner. It holds a flat list
    of all Factors that should be run."""

    factors: List[Factor] = field(default_factory=list)

    def next(self) -> Factor:
        """Return next pending factor from the bottom of the list"""
        factor_cls = self.factors.pop(0)
        return factor_cls


class FlowPlanner:
    """Execute all policies to plan out a flat list of all Factors
    that should be applied."""

    flow: Flow

    def __init__(self, flow: Flow):
        self.flow = flow

    def _check_flow_root_policies(self, request: HttpRequest) -> Tuple[bool, List[str]]:
        engine = PolicyEngine(self.flow.policies.all(), request.user, request)
        engine.build()
        return engine.result

    def plan(self, request: HttpRequest) -> FlowPlan:
        """Check each of the flows' policies, check policies for each factor with PolicyBinding
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
        for factor in self.flow.factors.order_by("order").select_subclasses():
            engine = PolicyEngine(factor.policies.all(), request.user, request)
            engine.build()
            passing, _ = engine.result
            if passing:
                LOGGER.debug("Factor passing", factor=factor)
                plan.factors.append(factor)
        end_time = time()
        LOGGER.debug(
            "Finished planning", flow=self.flow, duration_s=end_time - start_time
        )
        return plan
