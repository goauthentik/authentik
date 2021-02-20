"""email tests"""
from unittest.mock import MagicMock, patch

from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import Token, User
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.stages.email.models import EmailStage
from authentik.stages.email.stage import QS_KEY_TOKEN


class TestEmailStage(TestCase):
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

    def test_rendering(self):
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
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_without_user(self):
        """Test without pending user"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse(
            "authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

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

    def test_use_global_settings(self):
        """Test use_global_settings"""
        host = "some-unique-string"
        with self.settings(
            EMAIL_HOST=host, EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
        ):
            self.assertEqual(EmailStage(use_global_settings=True).backend.host, host)

    def test_token(self):
        """Test with token"""
        # Make sure token exists
        self.test_pending_user()
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        with patch("authentik.flows.views.FlowExecutorView.cancel", MagicMock()):
            # Call the executor shell to preseed the session
            url = reverse(
                "authentik_flows:flow-executor-shell",
                kwargs={"flow_slug": self.flow.slug},
            )
            token = Token.objects.get(user=self.user)
            url += f"?{QS_KEY_TOKEN}={token.pk.hex}"
            self.client.get(url)
            # Call the actual executor to get the JSON Response
            response = self.client.get(
                reverse(
                    "authentik_api:flow-executor",
                    kwargs={"flow_slug": self.flow.slug},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(
                force_str(response.content),
                {"type": "redirect", "to": reverse("authentik_core:shell")},
            )

            session = self.client.session
            plan: FlowPlan = session[SESSION_KEY_PLAN]
            self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER], self.user)
