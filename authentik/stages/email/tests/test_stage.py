"""email tests"""
from unittest.mock import MagicMock, PropertyMock, patch

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.urls import reverse
from django.utils.http import urlencode

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding, FlowToken
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import QS_KEY_TOKEN, SESSION_KEY_PLAN
from authentik.lib.config import CONFIG
from authentik.stages.email.models import EmailStage
from authentik.stages.email.stage import PLAN_CONTEXT_EMAIL_OVERRIDE


class TestEmailStage(FlowTestCase):
    """Email tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = EmailStage.objects.create(
            name="email",
            activate_user_on_success=True,
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_rendering(self):
        """Test with pending user"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @patch(
        "authentik.stages.email.models.EmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_rendering_locale(self):
        """Test with pending user"""
        self.user.attributes = {"settings": {"locale": "de"}}
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "authentik")
        self.assertNotIn("Password Reset", mail.outbox[0].alternatives[0][0])

    def test_without_user(self):
        """Test without pending user"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @patch(
        "authentik.stages.email.models.EmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_pending_user(self):
        """Test with pending user"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "authentik")
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    @patch(
        "authentik.stages.email.models.EmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_pending_user_override(self):
        """Test with pending user (override to)"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        plan.context[PLAN_CONTEXT_EMAIL_OVERRIDE] = "foo@bar.baz"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "authentik")
        self.assertEqual(mail.outbox[0].to, ["foo@bar.baz"])

    @patch(
        "authentik.stages.email.models.EmailStage.backend_class",
        PropertyMock(return_value=SMTPEmailBackend),
    )
    def test_use_global_settings(self):
        """Test use_global_settings"""
        host = "some-unique-string"
        with CONFIG.patch("email.host", host):
            self.assertEqual(EmailStage(use_global_settings=True).backend.host, host)

    def test_token(self):
        """Test with token"""
        # Make sure token exists
        self.test_pending_user()
        self.user.is_active = False
        self.user.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        token: FlowToken = FlowToken.objects.get(user=self.user)

        with patch("authentik.flows.views.executor.FlowExecutorView.cancel", MagicMock()):
            # Call the executor shell to preseed the session
            url = reverse(
                "authentik_api:flow-executor",
                kwargs={"flow_slug": self.flow.slug},
            )
            url_query = urlencode(
                {
                    QS_KEY_TOKEN: token.key,
                }
            )
            url += f"?query={url_query}"
            self.client.get(url)

            # Call the actual executor to get the JSON Response
            response = self.client.get(
                reverse(
                    "authentik_api:flow-executor",
                    kwargs={"flow_slug": self.flow.slug},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

            session = self.client.session
            plan: FlowPlan = session[SESSION_KEY_PLAN]
            self.assertEqual(plan.context[PLAN_CONTEXT_PENDING_USER], self.user)
            self.assertTrue(plan.context[PLAN_CONTEXT_PENDING_USER].is_active)

    def test_token_invalid_user(self):
        """Test with token with invalid user"""
        # Make sure token exists
        self.test_pending_user()
        self.user.is_active = False
        self.user.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        # Set flow token user to a different user
        token: FlowToken = FlowToken.objects.get(user=self.user)
        token.user = create_test_admin_user()
        token.save()

        with patch("authentik.flows.views.executor.FlowExecutorView.cancel", MagicMock()):
            # Call the executor shell to preseed the session
            url = reverse(
                "authentik_api:flow-executor",
                kwargs={"flow_slug": self.flow.slug},
            )
            url_query = urlencode(
                {
                    QS_KEY_TOKEN: token.key,
                }
            )
            url += f"?query={url_query}"
            self.client.get(url)

            # Call the actual executor to get the JSON Response
            response = self.client.get(
                reverse(
                    "authentik_api:flow-executor",
                    kwargs={"flow_slug": self.flow.slug},
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertStageResponse(response, component="ak-stage-access-denied")
