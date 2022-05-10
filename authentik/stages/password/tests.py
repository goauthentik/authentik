"""password tests"""
from unittest.mock import MagicMock, patch

from django.core.exceptions import PermissionDenied
from django.urls import reverse

from authentik.core.models import User
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_key
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.models import PasswordStage

MOCK_BACKEND_AUTHENTICATE = MagicMock(side_effect=PermissionDenied("test"))


class TestPasswordStage(FlowTestCase):
    """Password tests"""

    def setUp(self):
        super().setUp()
        self.password = generate_key()
        self.user = User.objects.create_user(
            username="unittest", email="test@beryju.org", password=self.password
        )

        self.flow = Flow.objects.create(
            name="test-password",
            slug="test-password",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = PasswordStage.objects.create(name="password", backends=[BACKEND_INBUILT])
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_without_user(self):
        """Test without user"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Still have to send the password so the form is valid
            {"password": self.password},
        )

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="Unknown error",
        )

    def test_recovery_flow_link(self):
        """Test link to the default recovery flow"""
        flow = Flow.objects.create(designation=FlowDesignation.RECOVERY, slug="qewrqerqr")

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(flow.slug, response.content.decode())

    def test_valid_password(self):
        """Test with a valid pending user and valid password"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Form data
            {"password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_invalid_password(self):
        """Test with a valid pending user and invalid password"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Form data
            {"password": self.password + "test"},
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_password_lockout(self):
        """Test with a valid pending user and invalid password (trigger logout counter)"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
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
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Form data
            {"password": self.password + "test"},
        )
        self.assertEqual(response.status_code, 200)
        # To ensure the plan has been cancelled, check SESSION_KEY_PLAN
        self.assertNotIn(SESSION_KEY_PLAN, self.client.session)

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    @patch(
        "authentik.core.auth.InbuiltBackend.authenticate",
        MOCK_BACKEND_AUTHENTICATE,
    )
    def test_permission_denied(self):
        """Test with a valid pending user and valid password.
        Backend is patched to return PermissionError"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            # Form data
            {"password": self.password + "test"},
        )

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
            error_message="Unknown error",
        )
