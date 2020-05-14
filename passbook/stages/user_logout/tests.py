"""logout tests"""
from django.shortcuts import reverse
from django.test import Client, TestCase

from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from passbook.stages.user_logout.forms import UserLogoutStageForm
from passbook.stages.user_logout.models import UserLogoutStage


class TestUserLogoutStage(TestCase):
    """Logout tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-logout",
            slug="test-logout",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = UserLogoutStage.objects.create(name="logout")
        FlowStageBinding.objects.create(flow=self.flow, stage=self.stage, order=2)

    def test_valid_password(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, stages=[self.stage])
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

    def test_form(self):
        """Test Form"""
        data = {"name": "test"}
        self.assertEqual(UserLogoutStageForm(data).is_valid(), True)
