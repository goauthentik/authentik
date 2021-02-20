"""email tests"""
from smtplib import SMTPException
from unittest.mock import MagicMock, patch

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.test import Client, TestCase
from django.urls import reverse

from authentik.core.models import User
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.stages.email.models import EmailStage


class TestEmailStageSending(TestCase):
    """Email tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="unittest", email="test@beryju.org"
        )
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-email",
            slug="test-email",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = EmailStage.objects.create(
            name="email",
        )
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_pending_user(self):
        """Test with pending user"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse(
            "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
        )
        with self.settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            response = self.client.post(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "authentik")

    def test_send_error(self):
        """Test error during sending (sending will be retried)"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse(
            "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
        )
        with self.settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
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
