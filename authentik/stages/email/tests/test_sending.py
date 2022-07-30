"""email tests"""
from smtplib import SMTPException
from unittest.mock import MagicMock, PropertyMock, patch

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.email.models import EmailStage


class TestEmailStageSending(APITestCase):
    """Email tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = EmailStage.objects.create(
            name="email",
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_pending_user(self):
        """Test with pending user"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        with patch(
            "authentik.stages.email.models.EmailStage.backend_class",
            PropertyMock(return_value=EmailBackend),
        ):
            response = self.client.post(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "authentik")
            events = Event.objects.filter(action=EventAction.EMAIL_SENT)
            self.assertEqual(len(events), 1)
            event = events.first()
            self.assertEqual(event.context["message"], f"Email to {self.user.email} sent")
            self.assertEqual(event.context["subject"], "authentik")
            self.assertEqual(event.context["to_email"], [self.user.email])
            self.assertEqual(event.context["from_email"], "system@authentik.local")

    def test_send_error(self):
        """Test error during sending (sending will be retried)"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        with patch(
            "authentik.stages.email.models.EmailStage.backend_class",
            PropertyMock(return_value=EmailBackend),
        ):
            with patch(
                "django.core.mail.backends.locmem.EmailBackend.send_messages",
                MagicMock(side_effect=[SMTPException, EmailBackend.send_messages]),
            ):
                response = self.client.post(url)
            response = self.client.post(url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(len(mail.outbox) >= 1)
            self.assertEqual(mail.outbox[0].subject, "authentik")
