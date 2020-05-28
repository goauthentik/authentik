"""flow planner tests"""
from unittest.mock import MagicMock, patch

from django.shortcuts import reverse
from django.test import RequestFactory, TestCase
from guardian.shortcuts import get_anonymous_user

from passbook.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import FlowPlanner
from passbook.policies.types import PolicyResult
from passbook.stages.dummy.models import DummyStage

POLICY_RESULT_MOCK = MagicMock(return_value=PolicyResult(False))
TIME_NOW_MOCK = MagicMock(return_value=3)


class TestFlowPlanner(TestCase):
    """Test planner logic"""

    def setUp(self):
        self.request_factory = RequestFactory()

    def test_empty_plan(self):
        """Test that empty plan raises exception"""
        flow = Flow.objects.create(
            name="test-empty",
            slug="test-empty",
            designation=FlowDesignation.AUTHENTICATION,
        )
        request = self.request_factory.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        with self.assertRaises(EmptyFlowException):
            planner = FlowPlanner(flow)
            planner.plan(request)

    @patch(
        "passbook.flows.planner.FlowPlanner._check_flow_root_policies",
        POLICY_RESULT_MOCK,
    )
    def test_non_applicable_plan(self):
        """Test that empty plan raises exception"""
        flow = Flow.objects.create(
            name="test-empty",
            slug="test-empty",
            designation=FlowDesignation.AUTHENTICATION,
        )
        request = self.request_factory.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        with self.assertRaises(FlowNonApplicableException):
            planner = FlowPlanner(flow)
            planner.plan(request)

    @patch("passbook.flows.planner.time", TIME_NOW_MOCK)
    def test_planner_cache(self):
        """Test planner cache"""
        flow = Flow.objects.create(
            name="test-cache",
            slug="test-cache",
            designation=FlowDesignation.AUTHENTICATION,
        )
        FlowStageBinding.objects.create(
            flow=flow, stage=DummyStage.objects.create(name="dummy"), order=0
        )
        request = self.request_factory.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        planner = FlowPlanner(flow)
        planner.plan(request)
        self.assertEqual(TIME_NOW_MOCK.call_count, 2)  # Start and end
        planner = FlowPlanner(flow)
        planner.plan(request)
        self.assertEqual(
            TIME_NOW_MOCK.call_count, 2
        )  # When taking from cache, time is not measured
