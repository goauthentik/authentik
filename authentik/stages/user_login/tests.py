"""login tests"""
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import User
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests.test_views import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.policies.http import AccessDeniedResponse
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.user_login.forms import UserLoginStageForm
from authentik.stages.user_login.models import UserLoginStage


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
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

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
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"to": reverse("authentik_core:root-redirect"), "type": "redirect"},
        )

    @patch(
        "authentik.flows.views.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
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
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, AccessDeniedResponse)

    @patch(
        "authentik.flows.views.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
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
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, AccessDeniedResponse)

    def test_form(self):
        """Test Form"""
        data = {"name": "test", "session_duration": "seconds=0"}
        self.assertEqual(UserLoginStageForm(data).is_valid(), True)
        data = {"name": "test", "session_duration": "123"}
        self.assertEqual(UserLoginStageForm(data).is_valid(), False)
