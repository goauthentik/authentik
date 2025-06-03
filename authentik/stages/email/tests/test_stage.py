"""email tests"""

from unittest.mock import MagicMock, PropertyMock, patch

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.test import RequestFactory
from django.urls import reverse
from django.utils.http import urlencode

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowDesignation, FlowStageBinding, FlowToken
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import QS_KEY_TOKEN, SESSION_KEY_PLAN, FlowExecutorView
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.stages.consent.stage import SESSION_KEY_CONSENT_TOKEN
from authentik.stages.email.models import EmailStage
from authentik.stages.email.stage import PLAN_CONTEXT_EMAIL_OVERRIDE, EmailStageView


class TestEmailStage(FlowTestCase):
    """Email tests"""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.user = create_test_admin_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = EmailStage.objects.create(
            name="email",
            activate_user_on_success=True,
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    @patch(
        "authentik.stages.email.models.EmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
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
        self.assertEqual(mail.outbox[0].to, [f"{self.user.name} <{self.user.email}>"])

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
        self.assertEqual(mail.outbox[0].to, [f"{self.user.name} <foo@bar.baz>"])

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
            self.assertStageResponse(response, self.flow, component="ak-stage-consent")
            response = self.client.post(
                reverse(
                    "authentik_api:flow-executor",
                    kwargs={"flow_slug": self.flow.slug},
                ),
                data={
                    "token": self.client.session[SESSION_KEY_CONSENT_TOKEN],
                },
                follow=True,
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
        token.revoke_on_execution = True
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

    def test_url_no_params(self):
        """Test generation of the URL in the EMail"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        request = self.factory.get(url)
        stage_view = EmailStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
            ),
            request=request,
        )
        self.assertEqual(stage_view.get_full_url(), f"http://testserver/if/flow/{self.flow.slug}/")

    def test_url_our_params(self):
        """Test that all of our parameters are passed to the URL correctly"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        request = self.factory.get(url)
        stage_view = EmailStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
            ),
            request=request,
        )
        token = generate_id()
        self.assertEqual(
            stage_view.get_full_url(**{QS_KEY_TOKEN: token}),
            f"http://testserver/if/flow/{self.flow.slug}/?flow_token={token}",
        )

    def test_url_existing_params(self):
        """Test to ensure that URL params are preserved in the URL being sent"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        url += "?query=" + urlencode({"foo": "bar"})
        request = self.factory.get(url)
        stage_view = EmailStageView(
            FlowExecutorView(
                request=request,
                flow=self.flow,
            ),
            request=request,
        )
        token = generate_id()
        self.assertEqual(
            stage_view.get_full_url(**{QS_KEY_TOKEN: token}),
            f"http://testserver/if/flow/{self.flow.slug}/?foo=bar&flow_token={token}",
        )
