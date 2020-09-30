"""flow views tests"""
from unittest.mock import MagicMock, PropertyMock, patch

from django.http import HttpRequest, HttpResponse
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils.encoding import force_str

from passbook.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from passbook.flows.markers import ReevaluateMarker, StageMarker
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import FlowPlan
from passbook.flows.views import NEXT_ARG_NAME, SESSION_KEY_PLAN
from passbook.lib.config import CONFIG
from passbook.policies.dummy.models import DummyPolicy
from passbook.policies.http import AccessDeniedResponse
from passbook.policies.models import PolicyBinding
from passbook.policies.types import PolicyResult
from passbook.stages.dummy.models import DummyStage

POLICY_RETURN_FALSE = PropertyMock(return_value=PolicyResult(False))
POLICY_RETURN_TRUE = MagicMock(return_value=PolicyResult(True))


def to_stage_response(request: HttpRequest, source: HttpResponse):
    """Mock for to_stage_response that returns the original response, so we can check
    inheritance and member attributes"""
    return source


TO_STAGE_RESPONSE_MOCK = MagicMock(side_effect=to_stage_response)


class TestFlowExecutor(TestCase):
    """Test views logic"""

    def setUp(self):
        self.client = Client()

    def test_existing_plan_diff_flow(self):
        """Check that a plan for a different flow cancels the current plan"""
        flow = Flow.objects.create(
            name="test-existing-plan-diff",
            slug="test-existing-plan-diff",
            designation=FlowDesignation.AUTHENTICATION,
        )
        stage = DummyStage.objects.create(name="dummy")
        plan = FlowPlan(
            flow_pk=flow.pk.hex + "a", stages=[stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        cancel_mock = MagicMock()
        with patch("passbook.flows.views.FlowExecutorView.cancel", cancel_mock):
            response = self.client.get(
                reverse(
                    "passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}
                ),
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(cancel_mock.call_count, 2)

    @patch(
        "passbook.flows.views.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    @patch(
        "passbook.policies.engine.PolicyEngine.result",
        POLICY_RETURN_FALSE,
    )
    def test_invalid_non_applicable_flow(self):
        """Tests that a non-applicable flow returns the correct error message"""
        flow = Flow.objects.create(
            name="test-non-applicable",
            slug="test-non-applicable",
            designation=FlowDesignation.AUTHENTICATION,
        )

        CONFIG.update_from_dict({"domain": "testserver"})
        response = self.client.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, AccessDeniedResponse)
        self.assertInHTML(FlowNonApplicableException.__doc__, response.rendered_content)

    @patch(
        "passbook.flows.views.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_invalid_empty_flow(self):
        """Tests that an empty flow returns the correct error message"""
        flow = Flow.objects.create(
            name="test-empty",
            slug="test-empty",
            designation=FlowDesignation.AUTHENTICATION,
        )

        CONFIG.update_from_dict({"domain": "testserver"})
        response = self.client.get(
            reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, AccessDeniedResponse)
        self.assertInHTML(EmptyFlowException.__doc__, response.rendered_content)

    def test_invalid_flow_redirect(self):
        """Tests that an invalid flow still redirects"""
        flow = Flow.objects.create(
            name="test-empty",
            slug="test-empty",
            designation=FlowDesignation.AUTHENTICATION,
        )

        CONFIG.update_from_dict({"domain": "testserver"})
        dest = "/unique-string"
        url = reverse("passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(url + f"?{NEXT_ARG_NAME}={dest}")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"type": "redirect", "to": dest},
        )

    def test_multi_stage_flow(self):
        """Test a full flow with multiple stages"""
        flow = Flow.objects.create(
            name="test-full",
            slug="test-full",
            designation=FlowDesignation.AUTHENTICATION,
        )
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy1"), order=0
        )
        FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy2"), order=1
        )

        exec_url = reverse(
            "passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}
        )
        # First Request, start planning, renders form
        response = self.client.get(exec_url)
        self.assertEqual(response.status_code, 200)
        # Check that two stages are in plan
        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        self.assertEqual(len(plan.stages), 2)
        # Second request, submit form, one stage left
        response = self.client.post(exec_url)
        # Second request redirects to the same URL
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, exec_url)
        # Check that two stages are in plan
        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        self.assertEqual(len(plan.stages), 1)

    def test_reevaluate_remove_last(self):
        """Test planner with re-evaluate (last stage is removed)"""
        flow = Flow.objects.create(
            name="test-default-context",
            slug="test-default-context",
            designation=FlowDesignation.AUTHENTICATION,
        )
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

        # Here we patch the dummy policy to evaluate to true so the stage is included
        with patch(
            "passbook.policies.dummy.models.DummyPolicy.passes", POLICY_RETURN_TRUE
        ):

            exec_url = reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}
            )
            # First request, run the planner
            response = self.client.get(exec_url)
            self.assertEqual(response.status_code, 200)

            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.stages[0], binding.stage)
            self.assertEqual(plan.stages[1], binding2.stage)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)

            # Second request, this passes the first dummy stage
            response = self.client.post(exec_url)
            self.assertEqual(response.status_code, 302)

        # third request, this should trigger the re-evaluate
        # We do this request without the patch, so the policy results in false
        response = self.client.post(exec_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_core:overview"))

    def test_reevaluate_remove_middle(self):
        """Test planner with re-evaluate (middle stage is removed)"""
        flow = Flow.objects.create(
            name="test-default-context",
            slug="test-default-context",
            designation=FlowDesignation.AUTHENTICATION,
        )
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
        binding3 = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy3"), order=2
        )

        PolicyBinding.objects.create(policy=false_policy, target=binding2, order=0)

        # Here we patch the dummy policy to evaluate to true so the stage is included
        with patch(
            "passbook.policies.dummy.models.DummyPolicy.passes", POLICY_RETURN_TRUE
        ):

            exec_url = reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}
            )
            # First request, run the planner
            response = self.client.get(exec_url)

            self.assertEqual(response.status_code, 200)
            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.stages[0], binding.stage)
            self.assertEqual(plan.stages[1], binding2.stage)
            self.assertEqual(plan.stages[2], binding3.stage)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)
            self.assertIsInstance(plan.markers[2], StageMarker)

            # Second request, this passes the first dummy stage
            response = self.client.post(exec_url)
            self.assertEqual(response.status_code, 302)

            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.stages[0], binding2.stage)
            self.assertEqual(plan.stages[1], binding3.stage)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], StageMarker)

        # third request, this should trigger the re-evaluate
        # We do this request without the patch, so the policy results in false
        response = self.client.post(exec_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"type": "redirect", "to": reverse("passbook_core:overview")},
        )

    def test_reevaluate_remove_consecutive(self):
        """Test planner with re-evaluate (consecutive stages are removed)"""
        flow = Flow.objects.create(
            name="test-default-context",
            slug="test-default-context",
            designation=FlowDesignation.AUTHENTICATION,
        )
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
        binding3 = FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name="dummy3"),
            order=2,
            re_evaluate_policies=True,
        )
        binding4 = FlowStageBinding.objects.create(
            target=flow, stage=DummyStage.objects.create(name="dummy4"), order=2
        )

        PolicyBinding.objects.create(policy=false_policy, target=binding2, order=0)
        PolicyBinding.objects.create(policy=false_policy, target=binding3, order=0)

        # Here we patch the dummy policy to evaluate to true so the stage is included
        with patch(
            "passbook.policies.dummy.models.DummyPolicy.passes", POLICY_RETURN_TRUE
        ):

            exec_url = reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": flow.slug}
            )
            # First request, run the planner
            response = self.client.get(exec_url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("dummy1", force_str(response.content))

            plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]

            self.assertEqual(plan.stages[0], binding.stage)
            self.assertEqual(plan.stages[1], binding2.stage)
            self.assertEqual(plan.stages[2], binding3.stage)
            self.assertEqual(plan.stages[3], binding4.stage)

            self.assertIsInstance(plan.markers[0], StageMarker)
            self.assertIsInstance(plan.markers[1], ReevaluateMarker)
            self.assertIsInstance(plan.markers[2], ReevaluateMarker)
            self.assertIsInstance(plan.markers[3], StageMarker)

        # Second request, this passes the first dummy stage
        response = self.client.post(exec_url)
        self.assertEqual(response.status_code, 302)

        # third request, this should trigger the re-evaluate
        # A get request will evaluate the policies and this will return stage 4
        # but it won't save it, hence we cant' check the plan
        response = self.client.get(exec_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("dummy4", force_str(response.content))

        # fourth request, this confirms the last stage (dummy4)
        # We do this request without the patch, so the policy results in false
        response = self.client.post(exec_url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"type": "redirect", "to": reverse("passbook_core:overview")},
        )
