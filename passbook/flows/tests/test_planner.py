"""flow planner tests"""
from unittest.mock import MagicMock, PropertyMock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.shortcuts import reverse
from django.test import RequestFactory, TestCase
from guardian.shortcuts import get_anonymous_user

from passbook.core.models import User
from passbook.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    FlowPlanner,
    ReevaluateMarker,
    StageMarker,
    cache_key,
)
from passbook.policies.dummy.models import DummyPolicy
from passbook.policies.models import PolicyBinding
from passbook.policies.types import PolicyResult
from passbook.stages.dummy.models import DummyStage

POLICY_RETURN_FALSE = PropertyMock(return_value=PolicyResult(False))
TIME_NOW_MOCK = MagicMock(return_value=3)

POLICY_RETURN_TRUE = MagicMock(return_value=PolicyResult(True))


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
        "passbook.policies.engine.PolicyEngine.result", POLICY_RETURN_FALSE,
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

    def test_planner_default_context(self):
        """Test planner with default_context"""
        flow = Flow.objects.create(
            name="test-default-context",
            slug="test-default-context",
            designation=FlowDesignation.AUTHENTICATION,
        )
        FlowStageBinding.objects.create(
            flow=flow, stage=DummyStage.objects.create(name="dummy"), order=0
        )

        user = User.objects.create(username="test-user")
        request = self.request_factory.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = user
        planner = FlowPlanner(flow)
        planner.plan(request, default_context={PLAN_CONTEXT_PENDING_USER: user})
        key = cache_key(flow, user)
        self.assertTrue(cache.get(key) is not None)

    def test_planner_marker_reevaluate(self):
        """Test that the planner creates the proper marker"""
        flow = Flow.objects.create(
            name="test-default-context",
            slug="test-default-context",
            designation=FlowDesignation.AUTHENTICATION,
        )

        FlowStageBinding.objects.create(
            flow=flow,
            stage=DummyStage.objects.create(name="dummy1"),
            order=0,
            re_evaluate_policies=True,
        )

        request = self.request_factory.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        planner = FlowPlanner(flow)
        plan = planner.plan(request)

        self.assertIsInstance(plan.markers[0], ReevaluateMarker)

    def test_planner_reevaluate_actual(self):
        """Test planner with re-evaluate"""
        flow = Flow.objects.create(
            name="test-default-context",
            slug="test-default-context",
            designation=FlowDesignation.AUTHENTICATION,
        )
        false_policy = DummyPolicy.objects.create(result=False, wait_min=1, wait_max=2)

        binding = FlowStageBinding.objects.create(
            flow=flow, stage=DummyStage.objects.create(name="dummy1"), order=0
        )
        binding2 = FlowStageBinding.objects.create(
            flow=flow,
            stage=DummyStage.objects.create(name="dummy2"),
            order=1,
            re_evaluate_policies=True,
        )

        PolicyBinding.objects.create(policy=false_policy, target=binding2, order=0)

        request = self.request_factory.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        # Here we patch the dummy policy to evaluate to true so the stage is included
        with patch(
            "passbook.policies.dummy.models.DummyPolicy.passes", POLICY_RETURN_TRUE
        ):
            planner = FlowPlanner(flow)
            plan = planner.plan(request)

            self.assertEqual(plan.stages[0], binding.stage)
            self.assertEqual(plan.stages[1], binding2.stage)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)
