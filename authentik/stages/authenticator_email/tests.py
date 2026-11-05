"""Test Email Authenticator API"""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

from django.core import mail
from django.core.cache import cache
from django.core.mail.backends.locmem import EmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.template.exceptions import TemplateDoesNotExist
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from authentik.core.models import User
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.flows.models import FlowStageBinding
from authentik.flows.tests import APIFlowTestCase
from authentik.lib.config import CONFIG
from authentik.lib.utils.email import mask_email
from authentik.stages.authenticator.tests import ThrottlingTestMixin
from authentik.stages.authenticator_email.api import (
    AuthenticatorEmailStageSerializer,
    EmailDeviceSerializer,
)
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage, EmailDevice
from authentik.stages.authenticator_email.stage import (
    PLAN_CONTEXT_EMAIL_DEVICE,
    AuthenticatorEmailStageView,
)
from authentik.stages.authenticator_validate.challenge import select_challenge_email
from authentik.stages.email.throttling import email_is_rate_limited
from authentik.stages.email.utils import TemplateEmailMessage


class TestAuthenticatorEmailStage(APIFlowTestCase):
    """Test Email Authenticator stage"""

    def setUp(self):
        super().setUp()
        self.flow = create_test_flow()
        self.user = create_test_user()
        self.user_noemail = create_test_user(email="")
        self.stage = AuthenticatorEmailStage.objects.create(
            name="email-authenticator",
            use_global_settings=True,
            from_address="test@authentik.local",
            configure_flow=self.flow,
            token_expiry="minutes=30",
        )  # nosec
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)
        self.device = EmailDevice.objects.create(
            user=self.user,
            stage=self.stage,
            email="test@authentik.local",
        )
        self.client.force_login(self.user)

    def test_device_str(self):
        """Test string representation of device"""
        self.assertEqual(str(self.device), f"Email Device for {self.user.pk}")
        # Test unsaved device
        unsaved_device = EmailDevice(
            user=self.user,
            stage=self.stage,
            email="test@authentik.local",
        )
        self.assertEqual(str(unsaved_device), "New Email Device")

    def test_stage_str(self):
        """Test string representation of stage"""
        self.assertEqual(str(self.stage), f"Email Authenticator Stage {self.stage.name}")

    def test_stage_deletion_is_protected(self):
        """A setup stage with enrolled devices cannot be deleted."""
        with self.assertRaises(ProtectedError):
            self.stage.delete()

        self.assertTrue(AuthenticatorEmailStage.objects.filter(pk=self.stage.pk).exists())
        self.assertTrue(EmailDevice.objects.filter(pk=self.device.pk).exists())

    def test_token_lifecycle(self):
        """Test token generation, validation and expiry"""
        # Initially no token
        self.assertIsNone(self.device.token)

        # Generate token
        self.device.generate_token()
        token = self.device.token
        self.assertIsNotNone(token)
        self.assertIsNotNone(self.device.valid_until)
        self.assertTrue(self.device.valid_until > now())

        # Verify invalid token
        self.assertFalse(self.device.verify_token("000000"))

        # Verify correct token (should clear token after verification)
        self.device.throttle_reset(commit=False)
        self.assertTrue(self.device.verify_token(token))
        self.assertIsNone(self.device.token)

    @patch(
        "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_stage_no_prefill(self):
        """Test stage without prefilled email"""
        self.client.force_login(self.user_noemail)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user_noemail,
            component="ak-stage-authenticator-email",
            email_required=True,
        )

    @patch(
        "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_stage_submit(self):
        """Test stage email submission"""
        # test fail because of existing device
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-access-denied",
        )
        self.device.delete()
        # Initialize the flow
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-email",
            email_required=False,
        )

        # The user already has an email on file, so the address is established by the flow
        # (email_required=False); an "email" in the request is ignored and the code is
        # (re)sent to the established address.
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"component": "ak-stage-authenticator-email", "email": "test@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        sent_mail = mail.outbox[1]
        self.assertEqual(sent_mail.subject, self.stage.subject)
        self.assertEqual(sent_mail.to, [f"{self.user} <{self.user.email}>"])
        self.assertNotIn("test@example.com", str(sent_mail.to))
        # Get from_address from global email config to test if global settings are being used
        from_address_global = CONFIG.get("email.from")
        self.assertEqual(sent_mail.from_email, from_address_global)

        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-email",
            response_errors={},
            email_required=False,
        )

    @patch(
        "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_email_uses_established_address(self):
        """A request-supplied email does not replace an address already set by the flow."""
        # The user has an email on file, so the flow establishes the address
        # (email_required=False) and the code is sent there on GET.
        self.device.delete()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-email",
            email_required=False,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [f"{self.user} <{self.user.email}>"])

        # A code-less submission that carries a different email must not change where the
        # code is sent.
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"component": "ak-stage-authenticator-email", "email": "other@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].to, [f"{self.user} <{self.user.email}>"])

        device = self.get_flow_plan().context[PLAN_CONTEXT_EMAIL_DEVICE]
        self.assertEqual(device.email, self.user.email)

    @patch(
        "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_submit_email_when_no_address_is_established(self):
        """A user without an email can request a code at the address they enter."""
        cache.clear()
        self.addCleanup(cache.clear)
        self.client.force_login(self.user_noemail)
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.get(url)
        self.assertStageResponse(response, self.flow, self.user_noemail, email_required=True)
        self.assertEqual(len(mail.outbox), 0)

        email = "otp@example.com"
        response = self.client.post(
            url, data={"component": "ak-stage-authenticator-email", "email": email}
        )
        self.assertStageResponse(
            response, self.flow, self.user_noemail, email_required=False, response_errors={}
        )
        device = self.get_flow_plan().context[PLAN_CONTEXT_EMAIL_DEVICE]
        self.assertEqual(device.email, email)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [f"{self.user_noemail} <{email}>"])
        self.assertIn(device.token, mail.outbox[0].body)
        self.user_noemail.refresh_from_db()
        self.assertEqual(self.user_noemail.email, "")

    @patch("authentik.stages.authenticator_email.stage.send_mails")
    def test_manual_email_is_not_assigned_when_sending_is_limited(self, send):
        """A rejected first send does not establish an address or rotate the token."""
        cache.clear()
        self.addCleanup(cache.clear)
        self.client.force_login(self.user_noemail)
        email = "otp@example.com"
        for _ in range(5):
            email_is_rate_limited(email)
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        self.client.get(url)
        device = self.get_flow_plan().context[PLAN_CONTEXT_EMAIL_DEVICE]
        token = device.token

        response = self.client.post(
            url, data={"component": "ak-stage-authenticator-email", "email": email}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["response_errors"]["non_field_errors"][0]["code"], "throttled"
        )
        device = self.get_flow_plan().context[PLAN_CONTEXT_EMAIL_DEVICE]
        self.assertEqual(device.email, "")
        self.assertEqual(device.token, token)
        send.assert_not_called()

    @patch("authentik.stages.authenticator_email.stage.send_mails")
    @patch.object(AuthenticatorEmailStageView, "get_pending_user")
    def test_unsaved_pending_user_is_denied(self, get_pending_user, send):
        """Unsaved users are denied before querying devices or attempting email delivery."""
        get_pending_user.return_value = User()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertStageResponse(response, self.flow, self.user, component="ak-stage-access-denied")
        send.assert_not_called()

    @patch("authentik.stages.authenticator_email.stage.send_mails")
    def test_prefilled_email_rate_limit_does_not_retry(self, send):
        """An exhausted shared window keeps the setup screen available for retry."""
        cache.clear()
        self.addCleanup(cache.clear)
        self.device.delete()
        for _ in range(5):
            email_is_rate_limited(self.user.email)
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.get(url)
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-email",
            email_required=False,
            response_errors={
                "non_field_errors": [
                    {
                        "code": "throttled",
                        "string": (
                            "Email sending was rate limited. Request a new code to try again."
                        ),
                    }
                ],
            },
        )
        send.assert_not_called()
        # Reloading must not turn an unsent token into a successful-send claim.
        response = self.client.get(url)
        self.assertEqual(
            response.json()["response_errors"]["non_field_errors"][0]["code"], "throttled"
        )
        response = self.client.post(url, data={"component": "ak-stage-authenticator-email"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["response_errors"]["non_field_errors"][0]["code"], "throttled"
        )
        send.assert_not_called()

    def test_email_template(self):
        """Test email template rendering"""
        self.device.generate_token()
        message = self.device._compose_email()

        self.assertIsInstance(message, TemplateEmailMessage)
        self.assertEqual(message.subject, self.stage.subject)
        self.assertEqual(message.to, [f"{self.user.name} <{self.device.email}>"])
        self.assertTrue(self.device.token in message.body)

    def test_duplicate_email(self):
        """Test attempting to use same email twice"""
        email = "test2@authentik.local"
        # First device
        EmailDevice.objects.create(
            user=self.user,
            stage=self.stage,
            email=email,
        )
        # Attempt to create second device with same email
        with self.assertRaises(IntegrityError):
            EmailDevice.objects.create(
                user=self.user,
                stage=self.stage,
                email=email,
            )

    def test_token_expiry(self):
        """Test token expiration behavior"""
        self.device.generate_token()
        token = self.device.token
        # Set token as expired
        self.device.valid_until = now() - timedelta(minutes=1)
        self.device.save()
        # Verify expired token fails
        self.assertFalse(self.device.verify_token(token))

    def test_template_errors(self):
        """Test handling of template errors"""
        self.stage.template = "{% invalid template %}"
        with self.assertRaises(TemplateDoesNotExist):
            self.stage.send(self.device)

    @patch(
        "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_challenge_response_validation(self):
        """Test challenge response validation"""
        # Initialize the flow
        self.client.force_login(self.user_noemail)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )

        # Test missing code and email
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"component": "ak-stage-authenticator-email"},
        )
        self.assertStageResponse(
            response,
            self.flow,
            response_errors={"non_field_errors": [{"code": "invalid", "string": "email required"}]},
        )

        # Test invalid code
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"component": "ak-stage-authenticator-email", "code": "000000"},
        )
        self.assertStageResponse(
            response,
            self.flow,
            response_errors={
                "non_field_errors": [{"code": "invalid", "string": "Code does not match"}]
            },
        )

        # Test valid code
        device = self.device
        token = device.token
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"component": "ak-stage-authenticator-email", "code": token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(device.confirmed)

    @patch(
        "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_challenge_generation(self):
        """Test challenge generation"""
        # Test with masked email
        self.device.delete()
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-email",
            email_required=False,
        )
        masked_email = mask_email(self.user.email)
        self.assertEqual(masked_email, response.json()["email"])
        self.client.logout()

        # Test without email
        self.client.force_login(self.user_noemail)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user_noemail,
            component="ak-stage-authenticator-email",
            email_required=True,
        )
        self.assertIsNone(response.json()["email"])

    @patch(
        "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_session_management(self):
        """Test session device management"""
        # Test device creation in session
        # Delete any existing devices for this test
        EmailDevice.objects.filter(user=self.user).delete()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        device = self.get_flow_plan().context[PLAN_CONTEXT_EMAIL_DEVICE]
        self.assertIsInstance(device, EmailDevice)
        self.assertFalse(device.confirmed)
        self.assertEqual(device.user, self.user)

        # Test device confirmation and cleanup
        device.confirmed = True
        device.email = "new_test@authentik.local"  # Use a different email
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"component": "ak-stage-authenticator-email", "code": device.token},
        )
        self.assertEqual(response.status_code, 200)

    def test_model_properties_and_methods(self):
        """Test model properties"""
        device = self.device
        stage = self.stage

        self.assertEqual(stage.serializer, AuthenticatorEmailStageSerializer)
        self.assertIsInstance(stage.backend, SMTPEmailBackend)
        self.assertEqual(device.serializer, EmailDeviceSerializer)

        # Test AuthenticatorEmailStage send method
        self.device.generate_token()
        # Test EmailDevice _compose_email method
        message = self.device._compose_email()
        self.assertIsInstance(message, TemplateEmailMessage)
        self.assertEqual(message.subject, self.stage.subject)
        self.assertEqual(message.to, [f"{self.user.name} <{self.device.email}>"])
        self.assertTrue(self.device.token in message.body)

    @patch(
        "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_email_tasks(self):
        # Test AuthenticatorEmailStage send method
        self.stage.send(self.device)
        self.assertEqual(len(mail.outbox), 1)


class TestEmailDeviceThrottling(ThrottlingTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        flow = create_test_flow()
        user = create_test_user()
        stage = AuthenticatorEmailStage.objects.create(
            name="email-authenticator-throttle",
            use_global_settings=True,
            from_address="test@authentik.local",
            configure_flow=flow,
            token_expiry="minutes=30",
        )  # nosec
        self.device = EmailDevice.objects.create(
            user=user, stage=stage, email="throttle@authentik.local"
        )
        self.device.generate_token()

    def valid_token(self):
        return self.device.token

    def invalid_token(self):
        return "000000" if self.device.token != "000000" else "111111"


class TestAuthenticatorEmailResendThrottle(TestCase):
    """Email OTP sends share the existing email stage's attempt window."""

    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)
        self.email = "otp@example.com"

    def test_shared_window_and_case_folding(self):
        for _ in range(5):
            self.assertIsNone(email_is_rate_limited(self.email))
        self.assertEqual(email_is_rate_limited("OTP@example.com"), 5)
        self.assertIsNone(email_is_rate_limited("other@example.com"))

    def test_window_expires(self):
        timestamp = now()
        with patch("authentik.stages.email.throttling.now", return_value=timestamp):
            for _ in range(5):
                self.assertIsNone(email_is_rate_limited(self.email))
        with patch(
            "authentik.stages.email.throttling.now",
            return_value=timestamp + timedelta(minutes=5),
        ):
            self.assertIsNone(email_is_rate_limited(self.email))

    def test_setup_resend_preserves_token_when_limited(self):
        device = EmailDevice(email=self.email, token="123456")
        view = AuthenticatorEmailStageView.__new__(AuthenticatorEmailStageView)
        view.executor = SimpleNamespace(
            current_stage=None, plan=SimpleNamespace(context={PLAN_CONTEXT_EMAIL_DEVICE: device})
        )
        for _ in range(5):
            email_is_rate_limited(self.email)
        with self.assertRaises(ValidationError):
            view.resend()
        self.assertEqual(device.token, "123456")

    def test_validation_resend_uses_shared_window(self):
        user = create_test_user()
        stage = AuthenticatorEmailStage.objects.create(name="email-otp", use_global_settings=True)
        device = EmailDevice.objects.create(user=user, stage=stage, email=self.email)
        with patch.object(AuthenticatorEmailStage, "send") as send:
            # Existing recovery attempts also count towards OTP sending.
            for _ in range(4):
                email_is_rate_limited(self.email)
            select_challenge_email(None, device)
            token = device.token
            with self.assertRaises(ValidationError):
                select_challenge_email(None, device)
            send.assert_called_once()
            device.refresh_from_db()
            self.assertEqual(device.token, token)

    def test_setup_allows_immediate_resends_within_shared_budget(self):
        device = EmailDevice(email=self.email)
        stage = SimpleNamespace(token_expiry="minutes=30")
        view = AuthenticatorEmailStageView.__new__(AuthenticatorEmailStageView)
        view.executor = SimpleNamespace(
            current_stage=stage,
            plan=SimpleNamespace(context={PLAN_CONTEXT_EMAIL_DEVICE: device}),
        )
        with patch.object(view, "_send_email") as send:
            for _ in range(5):
                view.resend()
            token = device.token
            with self.assertRaises(ValidationError):
                view.resend()
            self.assertEqual(send.call_count, 5)
            self.assertEqual(device.token, token)
