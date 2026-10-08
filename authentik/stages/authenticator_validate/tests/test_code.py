"""Code validation must respect stage and challenge restrictions."""

from django.test import TestCase
from django.test.client import RequestFactory
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.planner import FlowPlan
from authentik.flows.stage import StageView
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.stages.authenticator.oath import TOTP
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage, EmailDevice
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSDevice
from authentik.stages.authenticator_static.models import StaticDevice, StaticToken
from authentik.stages.authenticator_totp.models import TOTPDevice
from authentik.stages.authenticator_validate.challenge import validate_challenge_code
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.authenticator_validate.stage import PLAN_CONTEXT_DEVICE_CHALLENGES


@freeze_time("2026-10-08 12:00:00")
class ValidateChallengeCodeTests(TestCase):
    """Exercise real tokens for each code-based device class."""

    def setUp(self):
        self.user = create_test_admin_user()
        email_stage = AuthenticatorEmailStage.objects.create(name=generate_id())
        sms_stage = AuthenticatorSMSStage.objects.create(name=generate_id())
        self.devices = [
            EmailDevice.objects.create(user=self.user, stage=email_stage, email="test@0.co"),
            SMSDevice.objects.create(user=self.user, stage=sms_stage, phone_number="+15551230101"),
            TOTPDevice.objects.create(user=self.user),
            StaticDevice.objects.create(user=self.user),
        ]
        self.devices[0].generate_token()
        self.devices[1].generate_token()
        static_token = StaticToken.objects.create(device=self.devices[3], token=generate_id())
        self.tokens = [
            self.devices[0].token,
            self.devices[1].token,
            str(TOTP(self.devices[2].bin_key).token()),
            static_token.token,
        ]

    def _view(self, classes, challenges):
        stage = AuthenticatorValidateStage.objects.create(
            name=generate_id(), device_classes=classes
        )
        plan = FlowPlan(flow_pk=generate_id(), context={PLAN_CONTEXT_DEVICE_CHALLENGES: challenges})
        return StageView(
            FlowExecutorView(current_stage=stage, plan=plan),
            request=RequestFactory().get("/"),
        )

    def test_disallowed_classes(self):
        """Even an existing challenge cannot authorize a class excluded by the stage."""
        for device, token in zip(self.devices, self.tokens, strict=True):
            device_class = DeviceClasses.from_model_label(device.model_label())
            with self.subTest(device_class=device_class):
                view = self._view(
                    [DeviceClasses.WEBAUTHN],
                    [{"device_class": device_class, "device_uid": str(device.pk)}],
                )
                with self.assertRaises(ValidationError):
                    validate_challenge_code(token, view, self.user)
                device.refresh_from_db()
                self.assertEqual(device.throttling_failure_count, 0)
                # Rejection must not consume or otherwise invalidate the token.
                self.assertTrue(device.verify_token(token))

    def test_missing_challenge(self):
        """Allowed classes still require an issued challenge."""
        for device, token in zip(self.devices, self.tokens, strict=True):
            device_class = DeviceClasses.from_model_label(device.model_label())
            with self.subTest(device_class=device_class):
                with self.assertRaises(ValidationError):
                    validate_challenge_code(token, self._view([device_class], []), self.user)
                device.refresh_from_db()
                self.assertEqual(device.throttling_failure_count, 0)
                self.assertTrue(device.verify_token(token))

    def test_email_sms_require_matching_device(self):
        """A code from another device of the same class cannot satisfy the challenge."""
        for device, token in zip(self.devices[:2], self.tokens[:2], strict=True):
            device_class = DeviceClasses.from_model_label(device.model_label())
            with self.subTest(device_class=device_class):
                view = self._view(
                    [device_class],
                    [{"device_class": device_class, "device_uid": str(device.pk + 1)}],
                )
                with self.assertRaises(ValidationError):
                    validate_challenge_code(token, view, self.user)
                device.refresh_from_db()
                self.assertEqual(device.throttling_failure_count, 0)
                view.executor.plan.context[PLAN_CONTEXT_DEVICE_CHALLENGES][0]["device_uid"] = str(
                    device.pk
                )
                self.assertEqual(validate_challenge_code(token, view, self.user), device)

    def test_totp_static_challenges_are_class_wide(self):
        """A single challenge permits all enrolled devices of an allowed TOTP/static class."""
        for device, token in zip(self.devices[2:], self.tokens[2:], strict=True):
            device_class = DeviceClasses.from_model_label(device.model_label())
            with self.subTest(device_class=device_class):
                other = type(device).objects.create(user=self.user)
                view = self._view(
                    [DeviceClasses.TOTP, DeviceClasses.STATIC],
                    [{"device_class": device_class, "device_uid": str(other.pk)}],
                )
                self.assertEqual(validate_challenge_code(token, view, self.user), device)
