"""flow planner tests"""

from unittest.mock import MagicMock, Mock, PropertyMock, patch

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.http import HttpRequest
from django.shortcuts import redirect
from django.test import RequestFactory, TestCase
from django.urls import reverse
from guardian.shortcuts import get_anonymous_user

from authentik.blueprints.tests import reconcile_app
from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.crypto.generators import generate_id
from authentik.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from authentik.flows.markers import ReevaluateMarker, StageMarker
from authentik.flows.models import (
    FlowAuthenticationRequirement,
    FlowDesignation,
    FlowStageBinding,
    in_memory_stage,
)
from authentik.flows.planner import (
    PLAN_CONTEXT_IS_REDIRECTED,
    PLAN_CONTEXT_PENDING_USER,
    FlowPlanner,
    cache_key,
)
from authentik.flows.stage import StageView
from authentik.lib.tests.utils import dummy_get_response
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import Outpost
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.policies.types import PolicyResult
from authentik.root.middleware import ClientIPMiddleware
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

    def test_authentication(self):
        """Test flow authentication"""
        flow = create_test_flow()
        flow.authentication = FlowAuthenticationRequirement.NONE
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = AnonymousUser()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        planner.plan(request)

        with self.assertRaises(FlowNonApplicableException):
            flow.authentication = FlowAuthenticationRequirement.REQUIRE_AUTHENTICATED
            FlowPlanner(flow).plan(request)
        with self.assertRaises(FlowNonApplicableException):
            flow.authentication = FlowAuthenticationRequirement.REQUIRE_SUPERUSER
            FlowPlanner(flow).plan(request)

        request.user = create_test_admin_user()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        planner.plan(request)

    def test_authentication_redirect_required(self):
        """Test flow authentication (redirect required)"""
        flow = create_test_flow()
        flow.authentication = FlowAuthenticationRequirement.REQUIRE_REDIRECT
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = AnonymousUser()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True

        with self.assertRaises(FlowNonApplicableException):
            planner.plan(request)

        context = {}
        context[PLAN_CONTEXT_IS_REDIRECTED] = create_test_flow()
        planner.plan(request, context)

    @reconcile_app("authentik_outposts")
    def test_authentication_outpost(self):
        """Test flow authentication (outpost)"""
        flow = create_test_flow()
        flow.authentication = FlowAuthenticationRequirement.REQUIRE_OUTPOST
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = AnonymousUser()
        with self.assertRaises(FlowNonApplicableException):
            planner = FlowPlanner(flow)
            planner.allow_empty_flows = True
            planner.plan(request)

        outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            HTTP_X_AUTHENTIK_OUTPOST_TOKEN=outpost.token.key,
            HTTP_X_AUTHENTIK_REMOTE_IP="1.2.3.4",
        )
        request.user = AnonymousUser()
        middleware = ClientIPMiddleware(dummy_get_response)
        middleware(request)

        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
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
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
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
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
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
            stage=DummyStage.objects.create(name=generate_id()),
            order=0,
            re_evaluate_policies=True,
        )

        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = get_anonymous_user()

        planner = FlowPlanner(flow)
        plan = planner.plan(request)

        self.assertEqual(plan.markers[0].__class__, ReevaluateMarker)

    def test_planner_reevaluate_actual(self):
        """Test planner with re-evaluate"""
        flow = create_test_flow()
        false_policy = DummyPolicy.objects.create(result=False, wait_min=1, wait_max=2)

        binding = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=0,
            re_evaluate_policies=False,
        )
        binding2 = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
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

            self.assertEqual(plan.markers[0].__class__, StageMarker)
            self.assertEqual(plan.markers[1].__class__, ReevaluateMarker)
            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)

    def test_to_redirect(self):
        """Test to_redirect and skipping the flow executor"""
        flow = create_test_flow()
        flow.authentication = FlowAuthenticationRequirement.NONE
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

        request.user = AnonymousUser()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        plan = planner.plan(request)
        self.assertTrue(plan.requires_flow_executor())
        self.assertEqual(
            plan.to_redirect(request, flow).url,
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug}),
        )

    def test_to_redirect_skip_simple(self):
        """Test to_redirect and skipping the flow executor"""
        flow = create_test_flow()
        flow.authentication = FlowAuthenticationRequirement.NONE
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        request.user = AnonymousUser()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        plan = planner.plan(request)

        class TStageView(StageView):
            def dispatch(self, request: HttpRequest, *args, **kwargs):
                return redirect("https://authentik.company")

        plan.append_stage(in_memory_stage(TStageView))
        self.assertFalse(plan.requires_flow_executor(allowed_silent_types=[TStageView]))
        self.assertEqual(
            plan.to_redirect(request, flow, allowed_silent_types=[TStageView]).url,
            "https://authentik.company",
        )

    def test_to_redirect_skip_stage(self):
        """Test to_redirect and skipping the flow executor
        (with a stage bound that cannot be skipped)"""
        flow = create_test_flow()
        flow.authentication = FlowAuthenticationRequirement.NONE

        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy"), order=0
        )

        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = AnonymousUser()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        plan = planner.plan(request)

        class TStageView(StageView):
            def dispatch(self, request: HttpRequest, *args, **kwargs):
                return redirect("https://authentik.company")

        plan.append_stage(in_memory_stage(TStageView))
        self.assertTrue(plan.requires_flow_executor(allowed_silent_types=[TStageView]))

    def test_to_redirect_skip_policies(self):
        """Test to_redirect and skipping the flow executor
        (with a marker on the stage view type that can be skipped)

        Note that this is not actually used anywhere in the code, all stages that are dynamically
        added are statically added"""
        flow = create_test_flow()
        flow.authentication = FlowAuthenticationRequirement.NONE

        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = AnonymousUser()
        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        plan = planner.plan(request)

        class TStageView(StageView):
            def dispatch(self, request: HttpRequest, *args, **kwargs):
                return redirect("https://authentik.company")

        plan.append_stage(in_memory_stage(TStageView), ReevaluateMarker(None))
        self.assertTrue(plan.requires_flow_executor(allowed_silent_types=[TStageView]))
