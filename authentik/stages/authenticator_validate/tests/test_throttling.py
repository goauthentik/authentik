from django.test import TestCase
from django.test.client import RequestFactory
from django.urls.base import reverse
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowStageBinding
from authentik.flows.stage import StageView
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage, EmailDevice
from authentik.stages.authenticator_sms.models import (
    AuthenticatorSMSStage,
    SMSDevice,
    SMSProviders,
)
from authentik.stages.authenticator_validate.challenge import validate_challenge_code
from authentik.stages.authenticator_validate.models import (
    AuthenticatorValidateStage,
    DeviceClasses,
)
from authentik.stages.identification.models import IdentificationStage, UserFields


class DeviceClassesHelperTests(TestCase):
    """Tests for the DeviceClasses.from_model_label helper."""

    def test_from_model_label_all_classes(self):
        cases = {
            "authentik_stages_authenticator_email.emaildevice": DeviceClasses.EMAIL,
            "authentik_stages_authenticator_sms.smsdevice": DeviceClasses.SMS,
            "authentik_stages_authenticator_totp.totpdevice": DeviceClasses.TOTP,
            "authentik_stages_authenticator_static.staticdevice": DeviceClasses.STATIC,
            "authentik_stages_authenticator_duo.duodevice": DeviceClasses.DUO,
            "authentik_stages_authenticator_webauthn.webauthndevice": DeviceClasses.WEBAUTHN,
        }
        for label, expected in cases.items():
            with self.subTest(label=label):
                self.assertEqual(DeviceClasses.from_model_label(label), expected)


class AuthenticatorValidateStageFactorTests(TestCase):
    """Tests for AuthenticatorValidateStage.get_throttling_factor."""

    def test_per_class_factors_returned(self):
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            email_otp_throttling_factor=5,
            sms_otp_throttling_factor=6,
            totp_otp_throttling_factor=7,
            static_otp_throttling_factor=8,
        )
        self.assertEqual(stage.get_throttling_factor(DeviceClasses.EMAIL), 5)
        self.assertEqual(stage.get_throttling_factor(DeviceClasses.SMS), 6)
        self.assertEqual(stage.get_throttling_factor(DeviceClasses.TOTP), 7)
        self.assertEqual(stage.get_throttling_factor(DeviceClasses.STATIC), 8)

    def test_no_factor_for_webauthn_or_duo(self):
        stage = AuthenticatorValidateStage.objects.create(name=generate_id())
        self.assertIsNone(stage.get_throttling_factor(DeviceClasses.WEBAUTHN))
        self.assertIsNone(stage.get_throttling_factor(DeviceClasses.DUO))


class ValidateChallengeCodeThrottlingTests(FlowTestCase):
    """Tests for validate_challenge_code throttling behavior."""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()
        self.email_stage = AuthenticatorEmailStage.objects.create(
            name="email-stage-validate-throttle",
            use_global_settings=True,
            from_address="test@authentik.local",
            token_expiry="minutes=30",
        )  # nosec
        self.sms_stage = AuthenticatorSMSStage.objects.create(
            name="sms-stage-validate-throttle",
            provider=SMSProviders.GENERIC,
            from_number="1234",
        )

    def _validate_stage(self, **factors) -> AuthenticatorValidateStage:
        return AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            device_classes=[
                DeviceClasses.EMAIL,
                DeviceClasses.SMS,
                DeviceClasses.TOTP,
                DeviceClasses.STATIC,
            ],
            **factors,
        )

    def _stage_view(self, validate_stage: AuthenticatorValidateStage) -> StageView:
        request = self.request_factory.get("/")
        return StageView(FlowExecutorView(current_stage=validate_stage), request=request)

    def _email_device(self, email: str = "throttle@authentik.local") -> EmailDevice:
        return EmailDevice.objects.create(
            user=self.user,
            stage=self.email_stage,
            confirmed=True,
            email=email,
        )

    def _sms_device(self, phone_number: str = "+15551230101") -> SMSDevice:
        return SMSDevice.objects.create(
            user=self.user,
            stage=self.sms_stage,
            confirmed=True,
            phone_number=phone_number,
        )

    def test_stage_factor_applied_to_email_device(self):
        """The stage's email_otp_throttling_factor is pushed onto the device before verify."""
        stage = self._validate_stage(email_otp_throttling_factor=3)
        device = self._email_device()
        device.generate_token()
        with self.assertRaises(ValidationError):
            validate_challenge_code("000000", self._stage_view(stage), self.user)
        device.refresh_from_db()
        self.assertEqual(device.throttling_failure_count, 1)
        # verify_is_allowed must compute the delay using factor=3 (3 * 2^0 = 3s).
        device.set_throttle_factor(3)
        allowed, data = device.verify_is_allowed()
        self.assertFalse(allowed)
        required = data["locked_until"] - device.throttling_failure_timestamp
        self.assertAlmostEqual(required.total_seconds(), 3, places=3)

    def test_factor_zero_disables_throttling_end_to_end(self):
        """With email_otp_throttling_factor=0, repeated failures do not lock the device."""
        stage = self._validate_stage(email_otp_throttling_factor=0)
        device = self._email_device()
        device.generate_token()
        token = device.token
        for _ in range(10):
            with self.assertRaises(ValidationError):
                validate_challenge_code("000000", self._stage_view(stage), self.user)
        matched = validate_challenge_code(token, self._stage_view(stage), self.user)
        self.assertEqual(matched.pk, device.pk)

    def test_lockout_persists_across_calls(self):
        """
        A correct token on the second call is still blocked and does not increment the counter.
        """
        stage = self._validate_stage(email_otp_throttling_factor=1)
        device = self._email_device()
        device.generate_token()
        token = device.token
        invalid_token = "000000" if token != "000000" else "111111"  # nosec
        with self.assertRaises(ValidationError):
            validate_challenge_code(invalid_token, self._stage_view(stage), self.user)
        # Immediately try with the correct token: lockout still active, attempt must be rejected.
        with self.assertRaises(ValidationError):
            validate_challenge_code(token, self._stage_view(stage), self.user)
        device.refresh_from_db()
        # Token wasn't consumed (verification never ran), and counter didn't get incremented.
        self.assertEqual(device.token, token)
        self.assertEqual(device.throttling_failure_count, 1)


class ValidateStageThrottlingFlowTests(FlowTestCase):
    """End-to-end lockout behavior through the flow executor HTTP API."""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.email_stage = AuthenticatorEmailStage.objects.create(
            name="email-stage-flow-throttle",
            use_global_settings=True,
            from_address="test@authentik.local",
            token_expiry="minutes=30",
        )  # nosec
        self.ident_stage = IdentificationStage.objects.create(
            name=generate_id(),
            user_fields=[UserFields.USERNAME],
        )
        self.validate_stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(),
            device_classes=[DeviceClasses.EMAIL],
            email_otp_throttling_factor=1,
        )
        self.flow = create_test_flow()
        FlowStageBinding.objects.create(target=self.flow, stage=self.ident_stage, order=0)
        FlowStageBinding.objects.create(target=self.flow, stage=self.validate_stage, order=1)

    def _identify(self):
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"uid_field": self.user.username},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def _select_email(self, device: EmailDevice):
        self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {
                "component": "ak-stage-authenticator-validate",
                "selected_challenge": {
                    "device_class": "email",
                    "device_uid": str(device.pk),
                    "challenge": {},
                    "last_used": None,
                },
            },
        )

    def test_bad_code_then_correct_code_is_still_blocked(self):
        """After a bad code over HTTP, a subsequent correct code is still rejected
        because the lockout persists in the database."""
        device = EmailDevice.objects.create(
            user=self.user,
            confirmed=True,
            stage=self.email_stage,
            email="throttle-flow@authentik.local",
        )
        self._identify()
        self._select_email(device)
        # Server generated and stored the token - grab it from DB.
        device.refresh_from_db()
        token = device.token
        # First attempt: bad code - must increment the DB counter.
        self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"component": "ak-stage-authenticator-validate", "code": "000000"},
        )
        device.refresh_from_db()
        self.assertEqual(device.throttling_failure_count, 1)
        self.assertEqual(device.token, token)
        # Second attempt with the correct token - still blocked.
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"component": "ak-stage-authenticator-validate", "code": token},
        )
        self.assertStageResponse(
            response,
            flow=self.flow,
            component="ak-stage-authenticator-validate",
        )
        device.refresh_from_db()
        # Counter wasn't incremented on a blocked attempt
        self.assertEqual(device.throttling_failure_count, 1)
        # Token wasn't consumed.
        self.assertEqual(device.token, token)
