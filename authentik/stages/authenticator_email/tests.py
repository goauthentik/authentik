"""Test Email Authenticator API"""

from datetime import timedelta
from unittest.mock import PropertyMock, patch

from django.core import mail
from django.core.mail.backends.locmem import EmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.db.utils import IntegrityError
from django.template.exceptions import TemplateDoesNotExist
from django.urls import reverse
from django.utils.timezone import now

from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.flows.models import FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.lib.config import CONFIG
from authentik.lib.utils.email import mask_email
from authentik.stages.authenticator_email.api import (
    AuthenticatorEmailStageSerializer,
    EmailDeviceSerializer,
)
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage, EmailDevice
from authentik.stages.authenticator_email.stage import (
    SESSION_KEY_EMAIL_DEVICE,
)
from authentik.stages.email.utils import TemplateEmailMessage


class TestAuthenticatorEmailStage(FlowTestCase):
    """Test Email Authenticator stage"""

    def setUp(self):
        super().setUp()
        self.flow = create_test_flow()
        self.user = create_test_admin_user()
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

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"component": "ak-stage-authenticator-email", "email": "test@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        sent_mail = mail.outbox[1]
        self.assertEqual(sent_mail.subject, self.stage.subject)
        self.assertEqual(sent_mail.to, [f"{self.user} <test@example.com>"])
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
        self.assertIn("email required", str(response.content))

        # Test invalid code
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            data={"component": "ak-stage-authenticator-email", "code": "000000"},
        )
        self.assertIn("Code does not match", str(response.content))

        # Test valid code
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
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
        self.assertIn(SESSION_KEY_EMAIL_DEVICE, self.client.session)
        device = self.client.session[SESSION_KEY_EMAIL_DEVICE]
        self.assertIsInstance(device, EmailDevice)
        self.assertFalse(device.confirmed)
        self.assertEqual(device.user, self.user)

        # Test device confirmation and cleanup
        device.confirmed = True
        device.email = "new_test@authentik.local"  # Use a different email
        self.client.session[SESSION_KEY_EMAIL_DEVICE] = device
        self.client.session.save()
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
