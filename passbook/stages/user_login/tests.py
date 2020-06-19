"""login tests"""
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils.encoding import force_text

from passbook.core.models import User
from passbook.flows.markers import StageMarker
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from passbook.stages.user_login.forms import UserLoginStageForm
from passbook.stages.user_login.models import UserLoginStage


class TestUserLoginStage(TestCase):
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
        self.stage = UserLoginStage.objects.create(name="login")
        FlowStageBinding.objects.create(flow=self.flow, stage=self.stage, order=2)

    def test_valid_password(self):
        """Test with a valid pending user and backend"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
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

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            {"type": "redirect", "to": reverse("passbook_core:overview")},
        )

    def test_without_user(self):
        """Test a plan without any pending user, resulting in a denied"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            {"type": "redirect", "to": reverse("passbook_flows:denied")},
        )

    def test_without_backend(self):
        """Test a plan with pending user, without backend, resulting in a denied"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            {"type": "redirect", "to": reverse("passbook_flows:denied")},
        )

    def test_form(self):
        """Test Form"""
        data = {"name": "test"}
        self.assertEqual(UserLoginStageForm(data).is_valid(), True)
