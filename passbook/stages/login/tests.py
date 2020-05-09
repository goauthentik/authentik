"""login tests"""
from django.shortcuts import reverse
from django.test import Client, TestCase

from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.login.models import LoginStage
from passbook.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND


class TestLoginStage(TestCase):
    """Login tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-login",
            slug="test-login",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = LoginStage.objects.create(name="login")
        FlowStageBinding.objects.create(flow=self.flow, stage=self.stage, order=2)

    def test_valid_password(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(stages=[self.stage])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[
            PLAN_CONTEXT_AUTHENTICATION_BACKEND
        ] = "django.contrib.auth.backends.ModelBackend"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_core:overview"))

    def test_without_user(self):
        """Test a plan without any pending user, resulting in a denied"""
        plan = FlowPlan(stages=[self.stage])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_flows:denied"))

    def test_without_backend(self):
        """Test a plan with pending user, without backend, resulting in a denied"""
        plan = FlowPlan(stages=[self.stage])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("passbook_flows:denied"))
