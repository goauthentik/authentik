"""email tests"""

from hashlib import sha256
from unittest.mock import MagicMock, PropertyMock, patch

from django.contrib import messages
from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.urls import reverse
from django.utils.http import urlencode

from authentik.brands.models import Brand
from authentik.core.tests.utils import RequestFactory, create_test_admin_user, create_test_flow
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

    def test_get_cache_key(self):
        """Test to ensure that the correct cache key is returned."""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        request = self.factory.post(url)
        request.user = self.user
        request.session = session

        executor = FlowExecutorView(request=request, flow=self.flow)
        executor.plan = plan

        stage_view = EmailStageView(executor, request=request)

        cache_key = stage_view._get_cache_key()

        expected_hash = sha256(self.user.email.lower().encode("utf-8")).hexdigest()
        expected_cache_key = "goauthentik.io/stages/email/stage/" + expected_hash

        self.assertEqual(cache_key, expected_cache_key)

    def test_is_rate_limited_returns_none(self):
        """Test to ensure None is returned if the request shouldn't be rate limited."""
        self.stage.recovery_max_attempts = 2
        self.stage.recovery_cache_timeout = "minutes=10"
        self.stage.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        request = self.factory.post(url)
        request.user = self.user
        request.session = session

        executor = FlowExecutorView(request=request, flow=self.flow)
        executor.current_stage = self.stage
        executor.plan = plan

        stage_view = EmailStageView(executor, request=request)

        result = stage_view._is_rate_limited()
        self.assertIsNone(result)

    def test_is_rate_limited_returns_remaining_time(self):
        """Test to ensure the remaining time is returned if the request
        should be rate limited."""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        request = self.factory.post(url)
        request.user = self.user
        request.session = session

        executor = FlowExecutorView(request=request, flow=self.flow)
        executor.current_stage = self.stage
        executor.plan = plan

        stage_view = EmailStageView(executor, request=request)

        test_cases = [
            # 2 attempts within 2 minutes
            (2, "seconds=120", 2),
            # 4 attempts within 5 minutes
            (4, "minutes=5", 5),
            # 6 attempts within 5 minutes. Although 299 seconds is less than
            # 5 minutes, the user is intentionally shown "5 minutes". This is
            # because an initial rate limiting message like "Try again after 4 minutes"
            # can be confusing.
            (6, "seconds=299", 5),
        ]
        for test_case in test_cases:
            max_attempts, cache_timeout, minutes_remaining = test_case
            with self.subTest(
                f"Test recovery with {max_attempts} max attempts and "
                f"{cache_timeout} cache timeout seconds"
            ):
                self.stage.recovery_max_attempts = max_attempts
                self.stage.recovery_cache_timeout = cache_timeout
                self.stage.save()

                # Simulate multiple requests
                for _ in range(max_attempts):
                    stage_view._is_rate_limited()

                # The following request should be rate-limited
                result = stage_view._is_rate_limited()

                self.assertEqual(result, minutes_remaining)

    def _challenge_invalid_helper(self):
        """Helper to test the challenge_invalid() method."""
        self.stage.recovery_max_attempts = 1
        self.stage.recovery_cache_timeout = "seconds=300"
        self.stage.save()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        request = self.factory.get(url, user=self.user)
        request.session = session

        request.brand = Brand.objects.create(domain="foo-domain.com", default=True)

        executor = FlowExecutorView(request=request, flow=self.flow)
        executor.current_stage = self.stage
        executor.plan = plan

        stage_view = EmailStageView(executor, request=request)
        challenge_response = stage_view.get_response_instance(data={})
        challenge_response.is_valid()

        return challenge_response, stage_view, request

    def test_challenge_invalid_not_rate_limited(self):
        """Tests that the request is not rate limited and email is sent."""
        challenge_response, stage_view, request = self._challenge_invalid_helper()

        with patch.object(stage_view, "send_email") as mock_send_email:
            result = stage_view.challenge_invalid(challenge_response)

            self.assertEqual(result.status_code, 200)

            mock_send_email.assert_called_once()

            message_list = list(messages.get_messages(request))
            self.assertEqual(len(message_list), 1)
            self.assertEqual(
                "Email Successfully sent.",
                message_list[-1].message,
            )

    def test_challenge_invalid_returns_error_if_rate_limited(self):
        """Tests that an error is returned if the request is rate limited. Ensure
        that an email is not sent."""
        challenge_response, stage_view, request = self._challenge_invalid_helper()

        # Initial request that shouldn't be rate limited
        stage_view.challenge_invalid(challenge_response)

        with patch.object(stage_view, "send_email") as mock_send_email:
            # This next request should be rate limited
            result = stage_view.challenge_invalid(challenge_response)

            self.assertEqual(result.status_code, 200)

            mock_send_email.assert_not_called()

            message_list = list(messages.get_messages(request))
            self.assertEqual(len(message_list), 2)
            self.assertEqual(
                "Too many account verification attempts. Please try again after 5 minutes.",
                message_list[-1].message,
            )
