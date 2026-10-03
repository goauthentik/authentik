"""invitation tests"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user
from rest_framework.test import APITestCase
from yaml import safe_load

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.invitation.api import InvitationSendEmailSerializer, InvitationSerializer
from authentik.stages.invitation.models import Invitation, InvitationStage
from authentik.stages.invitation.stage import (
    PLAN_CONTEXT_INVITATION_TOKEN,
    PLAN_CONTEXT_PROMPT,
    QS_INVITATION_TOKEN_KEY,
)
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND


class TestInvitationStage(FlowTestCase):
    """Login tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = InvitationStage.objects.create(name="invitation")
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_without_invitation_fail(self):
        """Test without any invitation, continue_flow_without_invitation not set."""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = BACKEND_INBUILT
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertStageResponse(
            response,
            flow=self.flow,
            component="ak-stage-access-denied",
        )

    def test_without_invitation_continue(self):
        """Test without any invitation, continue_flow_without_invitation is set."""
        self.stage.continue_flow_without_invitation = True
        self.stage.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = BACKEND_INBUILT
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

        self.stage.continue_flow_without_invitation = False
        self.stage.save()

    def test_with_invitation_expired(self):
        """Test with invitation, expired"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        data = {"foo": "bar"}
        invite = Invitation.objects.create(
            created_by=get_anonymous_user(),
            fixed_data=data,
            expires=now() - timedelta(hours=1),
        )

        base_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        args = urlencode({QS_INVITATION_TOKEN_KEY: invite.pk.hex})
        response = self.client.get(base_url + f"?query={args}")

        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(
            response,
            flow=self.flow,
            component="ak-stage-access-denied",
        )

    def test_with_invitation_get(self):
        """Test with invitation, check data in session"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        data = {"foo": "bar"}
        invite = Invitation.objects.create(created_by=get_anonymous_user(), fixed_data=data)

        with patch("authentik.flows.views.executor.FlowExecutorView.cancel", MagicMock()):
            base_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            args = urlencode({QS_INVITATION_TOKEN_KEY: invite.pk.hex})
            response = self.client.get(base_url + f"?query={args}")

        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_PROMPT], data)

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_invalid_flow(self):
        """Test with invitation, invalid flow limit"""
        invalid_flow = create_test_flow(FlowDesignation.ENROLLMENT)
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        data = {"foo": "bar"}
        invite = Invitation.objects.create(
            created_by=get_anonymous_user(), fixed_data=data, flow=invalid_flow
        )

        with patch("authentik.flows.views.executor.FlowExecutorView.cancel", MagicMock()):
            base_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            args = urlencode({QS_INVITATION_TOKEN_KEY: invite.pk.hex})
            response = self.client.get(base_url + f"?query={args}")

        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]

        self.assertStageResponse(
            response,
            flow=self.flow,
            component="ak-stage-access-denied",
        )

    def test_with_invitation_prompt_data(self):
        """Test with invitation, check data in session"""
        data = {"foo": "bar"}
        invite = Invitation.objects.create(
            created_by=get_anonymous_user(), fixed_data=data, single_use=True
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PROMPT] = {PLAN_CONTEXT_INVITATION_TOKEN: invite.pk.hex}
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        with patch("authentik.flows.views.executor.FlowExecutorView.cancel", MagicMock()):
            base_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
            response = self.client.get(base_url, follow=True)

        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        self.assertEqual(
            plan.context[PLAN_CONTEXT_PROMPT], data | plan.context[PLAN_CONTEXT_PROMPT]
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.assertFalse(Invitation.objects.filter(pk=invite.pk))


class TestInvitationsAPI(APITestCase):
    """Test Invitations API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_invite_create(self):
        """Test Invitations creation endpoint"""
        response = self.client.post(
            reverse("authentik_api:invitation-list"),
            {"name": "test-token", "fixed_data": {}},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Invitation.objects.first().created_by, self.user)

    def test_invite_create_blueprint_context(self):
        """Test Invitations creation via blueprint context"""

        flow = create_test_flow(FlowDesignation.ENROLLMENT)
        data = {
            "name": "test-blueprint-invitation",
            "flow": flow.pk.hex,
            "single_use": True,
            "fixed_data": {"email": "test@example.com"},
        }
        serializer = InvitationSerializer(data=data, context={SERIALIZER_CONTEXT_BLUEPRINT: True})
        self.assertTrue(serializer.is_valid())
        invitation = serializer.save()
        self.assertEqual(invitation.created_by, get_anonymous_user())
        self.assertEqual(invitation.name, "test-blueprint-invitation")
        self.assertEqual(invitation.fixed_data, {"email": "test@example.com"})

    def test_send_email_no_addresses(self):
        """Test send_email endpoint with no email addresses"""
        flow = create_test_flow(FlowDesignation.ENROLLMENT)
        invite = Invitation.objects.create(
            name="test-invite",
            created_by=self.user,
            flow=flow,
        )

        response = self.client.post(
            reverse("authentik_api:invitation-send-email", kwargs={"pk": invite.pk}),
            {"email_addresses": []},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_send_email_no_flow(self):
        """Test send_email endpoint with invitation without flow"""
        invite = Invitation.objects.create(
            name="test-invite-no-flow",
            created_by=self.user,
            flow=None,
        )

        response = self.client.post(
            reverse("authentik_api:invitation-send-email", kwargs={"pk": invite.pk}),
            {"email_addresses": ["test@example.com"]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    @patch("authentik.stages.invitation.api.BaseEvaluator.expr_send_email")
    def test_send_email_success(self, mock_send_email: MagicMock):
        """Test send_email endpoint successfully queues emails"""
        flow = create_test_flow(FlowDesignation.ENROLLMENT)
        invite = Invitation.objects.create(
            name="test-invite",
            created_by=self.user,
            flow=flow,
        )

        response = self.client.post(
            reverse("authentik_api:invitation-send-email", kwargs={"pk": invite.pk}),
            {
                "email_addresses": ["user1@example.com", "user2@example.com"],
                "template": "email/invitation.html",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(mock_send_email.call_count, 2)

    @patch("authentik.stages.invitation.api.BaseEvaluator.expr_send_email")
    def test_send_email_with_cc_bcc(self, mock_send_email: MagicMock):
        """Test send_email endpoint with CC and BCC addresses"""
        flow = create_test_flow(FlowDesignation.ENROLLMENT)
        invite = Invitation.objects.create(
            name="test-invite",
            created_by=self.user,
            flow=flow,
        )

        response = self.client.post(
            reverse("authentik_api:invitation-send-email", kwargs={"pk": invite.pk}),
            {
                "email_addresses": ["user@example.com"],
                "cc_addresses": ["cc@example.com"],
                "bcc_addresses": ["bcc@example.com"],
                "template": "email/invitation.html",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args.kwargs
        self.assertEqual(call_kwargs["cc"], ["cc@example.com"])
        self.assertEqual(call_kwargs["bcc"], ["bcc@example.com"])

    @patch("authentik.stages.invitation.api.BaseEvaluator.expr_send_email")
    def test_send_email_context(self, mock_send_email: MagicMock):
        """Test send_email endpoint passes correct context to email"""
        flow = create_test_flow(FlowDesignation.ENROLLMENT)
        invite = Invitation.objects.create(
            name="test-invite",
            created_by=self.user,
            flow=flow,
        )

        response = self.client.post(
            reverse("authentik_api:invitation-send-email", kwargs={"pk": invite.pk}),
            {"email_addresses": ["user@example.com"]},
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args.kwargs
        self.assertIn("url", call_kwargs["context"])
        self.assertIn(str(invite.pk), call_kwargs["context"]["url"])
        self.assertIn(flow.slug, call_kwargs["context"]["url"])

    def _enrollment_invite(self) -> Invitation:
        flow = create_test_flow(FlowDesignation.ENROLLMENT)
        return Invitation.objects.create(
            name="test-invite",
            created_by=self.user,
            flow=flow,
        )

    def _html_alternative(self, message: EmailMultiAlternatives) -> str:
        for content, mimetype in message.alternatives:
            if mimetype == "text/html":
                return content
        self.fail("Rendered message has no HTML alternative")

    def _assert_rendered_invitation(self, message: EmailMultiAlternatives, invite: Invitation):
        """The shipped invitation template rendered, including the enrollment link."""
        self.assertIsNotNone(invite.flow)
        flow_slug = invite.flow.slug
        self.assertIn(str(invite.pk), message.body)
        self.assertIn(flow_slug, message.body)
        self.assertIn(QS_INVITATION_TOKEN_KEY, message.body)
        html = self._html_alternative(message)
        self.assertIn(str(invite.pk), html)
        self.assertIn(flow_slug, html)
        self.assertIn("Accept Invitation", html)

    @patch("authentik.stages.email.tasks.send_mails")
    def test_send_email_serializer_default_renders(self, mock_send_mails: MagicMock):
        """Serializer default is the shipped template and that template renders."""
        invite = self._enrollment_invite()
        serializer = InvitationSendEmailSerializer(data={"email_addresses": ["user@example.com"]})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["template"], "email/invitation.html")

        response = self.client.post(
            reverse("authentik_api:invitation-send-email", kwargs={"pk": invite.pk}),
            serializer.validated_data,
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        mock_send_mails.assert_called_once()
        stage, message = mock_send_mails.call_args.args
        self.assertIsNone(stage)
        self._assert_rendered_invitation(message, invite)

    @patch("authentik.stages.email.tasks.send_mails")
    def test_send_email_omitted_template_renders(self, mock_send_mails: MagicMock):
        """Omitting template matches a request that sends the serializer default."""
        invite = self._enrollment_invite()
        response = self.client.post(
            reverse("authentik_api:invitation-send-email", kwargs={"pk": invite.pk}),
            {"email_addresses": ["user@example.com"]},
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        mock_send_mails.assert_called_once()
        stage, message = mock_send_mails.call_args.args
        self.assertIsNone(stage)
        self._assert_rendered_invitation(message, invite)

    @patch("authentik.stages.email.tasks.send_mails")
    def test_send_email_explicit_template_and_copies(self, mock_send_mails: MagicMock):
        """An explicit template is rendered as given, with CC and BCC preserved."""
        invite = self._enrollment_invite()
        response = self.client.post(
            reverse("authentik_api:invitation-send-email", kwargs={"pk": invite.pk}),
            {
                "email_addresses": ["user@example.com"],
                "cc_addresses": ["cc@example.com"],
                "bcc_addresses": ["bcc@example.com"],
                "template": "email/account_confirmation.html",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        mock_send_mails.assert_called_once()
        _stage, message = mock_send_mails.call_args.args
        self.assertEqual(message.to, ["user@example.com"])
        self.assertEqual(message.cc, ["cc@example.com"])
        self.assertEqual(message.bcc, ["bcc@example.com"])
        self.assertIn(str(invite.pk), message.body)
        self.assertIn("Welcome!", message.body)
        html = self._html_alternative(message)
        self.assertIn("Confirm Account", html)
        self.assertIn(str(invite.pk), html)
        self.assertNotIn("Accept Invitation", html)

    def test_send_email_schema_template_default(self):
        """Published request schema default is the shipped invitation template."""
        response = self.client.get(reverse("authentik_api:schema"))
        self.assertEqual(response.status_code, 200)
        schema = safe_load(response.content.decode())
        template = schema["components"]["schemas"]["InvitationSendEmailRequest"]["properties"][
            "template"
        ]
        self.assertEqual(template["default"], "email/invitation.html")
