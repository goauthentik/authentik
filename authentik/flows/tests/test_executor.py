"""flow views tests"""
from unittest.mock import MagicMock, PropertyMock, patch

from django.http import HttpRequest, HttpResponse
from django.test.client import RequestFactory
from django.urls import reverse

from authentik.core.models import User
from authentik.core.tests.utils import create_test_flow
from authentik.flows.markers import ReevaluateMarker, StageMarker
from authentik.flows.models import (
    FlowDeniedAction,
    FlowDesignation,
    FlowStageBinding,
    InvalidResponseAction,
)
from authentik.flows.planner import FlowPlan, FlowPlanner
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER, StageView
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_PLAN, FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.policies.reputation.models import ReputationPolicy
from authentik.policies.types import PolicyResult
from authentik.stages.deny.models import DenyStage
from authentik.stages.dummy.models import DummyStage
from authentik.stages.identification.models import IdentificationStage, UserFields

POLICY_RETURN_FALSE = PropertyMock(return_value=PolicyResult(False, "foo"))
POLICY_RETURN_TRUE = MagicMock(return_value=PolicyResult(True))


def to_stage_response(request: HttpRequest, source: HttpResponse):
    """Mock for to_stage_response that returns the original response, so we can check
    inheritance and member attributes"""
    return source


TO_STAGE_RESPONSE_MOCK = MagicMock(side_effect=to_stage_response)


class TestFlowExecutor(FlowTestCase):
    """Test executor"""

    def setUp(self):
        self.request_factory = RequestFactory()

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_existing_plan_diff_flow(self):
        """Check that a plan for a different flow cancels the current plan"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )
        stage = DummyStage.objects.create(name=generate_id())
        binding = FlowStageBinding(target=flow, stage=stage, order=0)
        plan = FlowPlan(flow_pk=flow.pk.hex + "a", bindings=[binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        cancel_mock = MagicMock()
        with patch("authentik.flows.views.executor.FlowExecutorView.cancel", cancel_mock):
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(cancel_mock.call_count, 2)

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    @patch(
        "authentik.policies.engine.PolicyEngine.result",
        POLICY_RETURN_FALSE,
    )
    def test_invalid_non_applicable_flow(self):
        """Tests that a non-applicable flow returns the correct error message"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertStageResponse(
            response,
            flow=flow,
            error_message="foo",
            component="ak-stage-access-denied",
        )

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    @patch(
        "authentik.policies.engine.PolicyEngine.result",
        POLICY_RETURN_FALSE,
    )
    def test_invalid_non_applicable_flow_continue(self):
        """Tests that a non-applicable flow that should redirect"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
            denied_action=FlowDeniedAction.CONTINUE,
        )

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("authentik_core:root-redirect"))

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_invalid_flow_redirect(self):
        """Tests that an invalid flow still redirects"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )

        dest = "/unique-string"
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(url + f"?{NEXT_ARG_NAME}={dest}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("authentik_core:root-redirect"))

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_invalid_empty_flow(self):
        """Tests that an empty flow returns the correct error message"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("authentik_core:root-redirect"))

    def test_multi_stage_flow(self):
        """Test a full flow with multiple stages"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
        )
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=1
        )

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        # First Request, start planning, renders form
        response = self.client.get(exec_url)
        self.assertEqual(response.status_code, 200)
        # Check that two stages are in plan
        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        self.assertEqual(len(plan.bindings), 2)
        # Second request, submit form, one stage left
        response = self.client.post(exec_url)
        # Second request redirects to the same URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, exec_url)
        # Check that two stages are in plan
        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        self.assertEqual(len(plan.bindings), 1)

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_reevaluate_remove_last(self):
        """Test planner with re-evaluate (last stage is removed)"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )
        false_policy = DummyPolicy.objects.create(
            name=generate_id(), result=False, wait_min=1, wait_max=2
        )

        binding = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
        )
        binding2 = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=1,
            re_evaluate_policies=True,
        )

        PolicyBinding.objects.create(policy=false_policy, target=binding2, order=0)

        # Here we patch the dummy policy to evaluate to true so the stage is included
        with patch("authentik.policies.dummy.models.DummyPolicy.passes", POLICY_RETURN_TRUE):
            exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
            # First request, run the planner
            response = self.client.get(exec_url)
            self.assertEqual(response.status_code, 200)

            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.bindings[0], binding)
            self.assertEqual(plan.bindings[1], binding2)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)

            # Second request, this passes the first dummy stage
            response = self.client.post(exec_url)
            self.assertEqual(response.status_code, 302)

        # third request, this should trigger the re-evaluate
        # We do this request without the patch, so the policy results in false
        response = self.client.post(exec_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("authentik_core:root-redirect"))

    def test_reevaluate_remove_middle(self):
        """Test planner with re-evaluate (middle stage is removed)"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )
        false_policy = DummyPolicy.objects.create(
            name=generate_id(), result=False, wait_min=1, wait_max=2
        )

        binding = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
        )
        binding2 = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=1,
            re_evaluate_policies=True,
        )
        binding3 = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=2
        )

        PolicyBinding.objects.create(policy=false_policy, target=binding2, order=0)

        # Here we patch the dummy policy to evaluate to true so the stage is included
        with patch("authentik.policies.dummy.models.DummyPolicy.passes", POLICY_RETURN_TRUE):
            exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
            # First request, run the planner
            response = self.client.get(exec_url)

            self.assertEqual(response.status_code, 200)
            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.bindings[0], binding)
            self.assertEqual(plan.bindings[1], binding2)
            self.assertEqual(plan.bindings[2], binding3)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)
            self.assertIsInstance(plan.markers[2], StageMarker)

            # Second request, this passes the first dummy stage
            response = self.client.post(exec_url)
            self.assertEqual(response.status_code, 302)

            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.bindings[0], binding2)
            self.assertEqual(plan.bindings[1], binding3)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], StageMarker)

        # third request, this should trigger the re-evaluate
        # We do this request without the patch, so the policy results in false
        response = self.client.post(exec_url)
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_reevaluate_keep(self):
        """Test planner with re-evaluate (everything is kept)"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )
        true_policy = DummyPolicy.objects.create(
            name=generate_id(), result=True, wait_min=1, wait_max=2
        )

        binding = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
        )
        binding2 = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=1,
            re_evaluate_policies=True,
        )
        binding3 = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=2
        )

        PolicyBinding.objects.create(policy=true_policy, target=binding2, order=0)

        # Here we patch the dummy policy to evaluate to true so the stage is included
        with patch("authentik.policies.dummy.models.DummyPolicy.passes", POLICY_RETURN_TRUE):
            exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
            # First request, run the planner
            response = self.client.get(exec_url)

            self.assertEqual(response.status_code, 200)
            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.bindings[0], binding)
            self.assertEqual(plan.bindings[1], binding2)
            self.assertEqual(plan.bindings[2], binding3)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)
            self.assertIsInstance(plan.markers[2], StageMarker)

            # Second request, this passes the first dummy stage
            response = self.client.post(exec_url)
            self.assertEqual(response.status_code, 302)

            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.bindings[0], binding2)
            self.assertEqual(plan.bindings[1], binding3)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], StageMarker)

            # Third request, this passes the first dummy stage
            response = self.client.post(exec_url)
            self.assertEqual(response.status_code, 302)

            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.bindings[0], binding3)

            self.assertIsInstance(plan.markers[0], StageMarker)

        # third request, this should trigger the re-evaluate
        # We do this request without the patch, so the policy results in false
        response = self.client.post(exec_url)
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_reevaluate_remove_consecutive(self):
        """Test planner with re-evaluate (consecutive stages are removed)"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )
        false_policy = DummyPolicy.objects.create(
            name=generate_id(), result=False, wait_min=1, wait_max=2
        )

        binding = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
        )
        binding2 = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=1,
            re_evaluate_policies=True,
        )
        binding3 = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=2,
            re_evaluate_policies=True,
        )
        binding4 = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=2
        )

        PolicyBinding.objects.create(policy=false_policy, target=binding2, order=0)
        PolicyBinding.objects.create(policy=false_policy, target=binding3, order=0)

        # Here we patch the dummy policy to evaluate to true so the stage is included
        with patch("authentik.policies.dummy.models.DummyPolicy.passes", POLICY_RETURN_TRUE):
            exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
            # First request, run the planner
            response = self.client.get(exec_url)
            self.assertEqual(response.status_code, 200)
            self.assertStageResponse(response, flow, component="ak-stage-dummy")

            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.bindings[0], binding)
            self.assertEqual(plan.bindings[1], binding2)
            self.assertEqual(plan.bindings[2], binding3)
            self.assertEqual(plan.bindings[3], binding4)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)
            self.assertIsInstance(plan.markers[2], ReevaluateMarker)
            self.assertIsInstance(plan.markers[3], StageMarker)

        # Second request, this passes the first dummy stage
        response = self.client.post(exec_url)
        self.assertEqual(response.status_code, 302)

        # third request, this should trigger the re-evaluate
        # A get request will evaluate the policies and this will return stage 4
        # but it won't save it, hence we can't check the plan
        response = self.client.get(exec_url)
        self.assertStageResponse(response, flow, component="ak-stage-dummy")

        # fourth request, this confirms the last stage (dummy4)
        # We do this request without the patch, so the policy results in false
        response = self.client.post(exec_url)
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_stageview_user_identifier(self):
        """Test PLAN_CONTEXT_PENDING_USER_IDENTIFIER"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name=generate_id()), order=0
        )

        ident = "test-identifier"

        user = User.objects.create(username="test-user")
        request = self.request_factory.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        request.user = user
        planner = FlowPlanner(flow)
        plan = planner.plan(request, default_context={PLAN_CONTEXT_PENDING_USER_IDENTIFIER: ident})

        executor = FlowExecutorView()
        executor.plan = plan
        executor.flow = flow

        stage_view = StageView(executor)
        self.assertEqual(ident, stage_view.get_pending_user(for_display=True).username)

    def test_invalid_restart(self):
        """Test flow that restarts on invalid entry"""
        flow = create_test_flow(
            FlowDesignation.AUTHENTICATION,
        )
        # Stage 0 is a deny stage that is added dynamically
        # when the reputation policy says so
        deny_stage = DenyStage.objects.create(name="deny")
        reputation_policy = ReputationPolicy.objects.create(
            name="reputation", threshold=-1, check_ip=False
        )
        deny_binding = FlowStageBinding.objects.create(
            target=flow,
            stage=deny_stage,
            order=0,
            evaluate_on_plan=False,
            re_evaluate_policies=True,
        )
        PolicyBinding.objects.create(policy=reputation_policy, target=deny_binding, order=0)

        # Stage 1 is an identification stage
        ident_stage = IdentificationStage.objects.create(
            name="ident",
            user_fields=[UserFields.E_MAIL],
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=ident_stage,
            order=1,
            invalid_response_action=InvalidResponseAction.RESTART_WITH_CONTEXT,
        )
        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        # First request, run the planner
        response = self.client.get(exec_url)
        self.assertStageResponse(
            response,
            flow,
            component="ak-stage-identification",
            password_fields=False,
            primary_action="Log in",
            sources=[],
            show_source_labels=False,
            user_fields=[UserFields.E_MAIL],
        )
        response = self.client.post(exec_url, {"uid_field": "invalid-string"}, follow=True)
        self.assertStageResponse(response, flow, component="ak-stage-access-denied")
