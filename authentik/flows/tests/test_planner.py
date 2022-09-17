"""flow planner tests"""
from unittest.mock import MagicMock, Mock, PropertyMock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import User
from authentik.core.tests.utils import create_test_flow
from authentik.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from authentik.flows.markers import ReevaluateMarker, StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner, cache_key
from authentik.lib.tests.utils import dummy_get_response
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.policies.types import PolicyResult
from authentik.stages.dummy.models import DummyStage

POLICY_RETURN_FALSE = PropertyMock(return_value=PolicyResult(False))
CACHE_MOCK = Mock(wraps=cache)

POLICY_RETURN_TRUE = MagicMock(return_value=PolicyResult(True))


class TestFlowPlanner(TestCase):
    """Test planner logic"""

    def setUp(self):
        self.request_factory = RequestFactory()

    def test_empty_plan(self):
        """Test that empty plan raises exception"""
        flow = create_test_flow()
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        with self.assertRaises(EmptyFlowException):
            planner = FlowPlanner(flow)
            planner.plan(request)

    @patch(
        "authentik.policies.engine.PolicyEngine.result",
        POLICY_RETURN_FALSE,
    )
    def test_non_applicable_plan(self):
        """Test that empty plan raises exception"""
        flow = create_test_flow()
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        with self.assertRaises(FlowNonApplicableException):
            planner = FlowPlanner(flow)
            planner.plan(request)

    @patch("authentik.flows.planner.cache", CACHE_MOCK)
    def test_planner_cache(self):
        """Test planner cache"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy"), order=0
        )
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        planner = FlowPlanner(flow)
        planner.plan(request)
        self.assertEqual(CACHE_MOCK.set.call_count, 1)  # Ensure plan is written to cache
        planner = FlowPlanner(flow)
        planner.plan(request)
        self.assertEqual(CACHE_MOCK.set.call_count, 1)  # Ensure nothing is written to cache
        self.assertEqual(CACHE_MOCK.get.call_count, 2)  # Get is called twice

    def test_planner_default_context(self):
        """Test planner with default_context"""
        flow = create_test_flow()
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy"), order=0
        )

        user = User.objects.create(username="test-user")
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = user
        planner = FlowPlanner(flow)
        planner.plan(request, default_context={PLAN_CONTEXT_PENDING_USER: user})
        key = cache_key(flow, user)
        self.assertTrue(cache.get(key) is not None)

    def test_planner_marker_reevaluate(self):
        """Test that the planner creates the proper marker"""
        flow = create_test_flow()

        FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name="dummy1"),
            order=0,
            re_evaluate_policies=True,
        )

        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        planner = FlowPlanner(flow)
        plan = planner.plan(request)

        self.assertIsInstance(plan.markers[0], ReevaluateMarker)

    def test_planner_reevaluate_actual(self):
        """Test planner with re-evaluate"""
        flow = create_test_flow()
        false_policy = DummyPolicy.objects.create(result=False, wait_min=1, wait_max=2)

        binding = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy1"), order=0
        )
        binding2 = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name="dummy2"),
            order=1,
            re_evaluate_policies=True,
        )

        PolicyBinding.objects.create(policy=false_policy, target=binding2, order=0)

        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

        # Here we patch the dummy policy to evaluate to true so the stage is included
        with patch("authentik.policies.dummy.models.DummyPolicy.passes", POLICY_RETURN_TRUE):
            planner = FlowPlanner(flow)
            plan = planner.plan(request)

            self.assertEqual(plan.bindings[0], binding)
            self.assertEqual(plan.bindings[1], binding2)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)
