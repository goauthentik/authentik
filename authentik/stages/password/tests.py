"""password tests"""
import string
from random import SystemRandom
from unittest.mock import MagicMock, patch

from django.core.exceptions import PermissionDenied
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
from authentik.stages.password.models import PasswordStage

MOCK_BACKEND_AUTHENTICATE = MagicMock(side_effect=PermissionDenied("test"))


class TestPasswordStage(TestCase):
    """Password tests"""

    def setUp(self):
        super().setUp()
        self.password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )
        self.user = User.objects.create_user(
            username="unittest", email="test@beryju.org", password=self.password
        )
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-password",
            slug="test-password",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = PasswordStage.objects.create(
            name="password", backends=["django.contrib.auth.backends.ModelBackend"]
        )
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    @patch(
        "authentik.flows.views.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_without_user(self):
        """Test without user"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            # Still have to send the password so the form is valid
            {"password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, AccessDeniedResponse)

    def test_recovery_flow_link(self):
        """Test link to the default recovery flow"""
        flow = Flow.objects.create(
            designation=FlowDesignation.RECOVERY, slug="qewrqerqr"
        )

        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(flow.slug, force_str(response.content))

    def test_valid_password(self):
        """Test with a valid pending user and valid password"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            # Form data
            {"password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"to": reverse("authentik_core:root-redirect"), "type": "redirect"},
        )

    def test_invalid_password(self):
        """Test with a valid pending user and invalid password"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            # Form data
            {"password": self.password + "test"},
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_password_lockout(self):
        """Test with a valid pending user and invalid password (trigger logout counter)"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        for _ in range(self.stage.failed_attempts_before_cancel):
            response = self.client.post(
                reverse(
                    "authentik_api:flow-executor",
                    kwargs={"flow_slug": self.flow.slug},
                ),
                # Form data
                {"password": self.password + "test"},
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            # Form data
            {"password": self.password + "test"},
        )
        self.assertEqual(response.status_code, 200)
        # To ensure the plan has been cancelled, check SESSION_KEY_PLAN
        self.assertNotIn(SESSION_KEY_PLAN, self.client.session)

    @patch(
        "authentik.flows.views.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    @patch(
        "django.contrib.auth.backends.ModelBackend.authenticate",
        MOCK_BACKEND_AUTHENTICATE,
    )
    def test_permission_denied(self):
        """Test with a valid pending user and valid password.
        Backend is patched to return PermissionError"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse(
                "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
            ),
            # Form data
            {"password": self.password + "test"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, AccessDeniedResponse)
