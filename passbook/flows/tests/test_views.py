"""flow views tests"""
from unittest.mock import MagicMock, PropertyMock, patch

from django.shortcuts import reverse
from django.test import Client, TestCase

from passbook.flows.exceptions import EmptyFlowException, FlowNonApplicableException
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import FlowPlan
from passbook.flows.views import NEXT_ARG_NAME, SESSION_KEY_PLAN
from passbook.lib.config import CONFIG
from passbook.policies.types import PolicyResult
from passbook.stages.dummy.models import DummyStage

POLICY_RESULT_MOCK = PropertyMock(return_value=PolicyResult(False))


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
        plan = FlowPlan(flow_pk=flow.pk.hex + "a", stages=[stage])
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
            self.assertEqual(response.status_code, 400)
            self.assertEqual(cancel_mock.call_count, 1)

    @patch(
        "passbook.policies.engine.PolicyEngine.result", POLICY_RESULT_MOCK,
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
        self.assertEqual(response.status_code, 400)
        self.assertInHTML(FlowNonApplicableException.__doc__, response.rendered_content)

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
        self.assertEqual(response.status_code, 400)
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
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, dest)

    def test_multi_stage_flow(self):
        """Test a full flow with multiple stages"""
        flow = Flow.objects.create(
            name="test-full",
            slug="test-full",
            designation=FlowDesignation.AUTHENTICATION,
        )
        FlowStageBinding.objects.create(
            flow=flow, stage=DummyStage.objects.create(name="dummy1"), order=0
        )
        FlowStageBinding.objects.create(
            flow=flow, stage=DummyStage.objects.create(name="dummy2"), order=1
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
