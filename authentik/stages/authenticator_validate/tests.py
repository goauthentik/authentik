"""Test validator stage"""
from unittest.mock import MagicMock, patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.exceptions import ValidationError

from authentik.core.models import User
from authentik.flows.models import NotConfiguredAction
from authentik.flows.tests.test_planner import dummy_get_response
from authentik.providers.oauth2.generators import (
    generate_client_id,
    generate_client_secret,
)
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.api import (
    AuthenticatorValidateStageSerializer,
)
from authentik.stages.authenticator_validate.challenge import (
    get_challenge_for_device,
    validate_challenge_code,
    validate_challenge_duo,
    validate_challenge_webauthn,
)
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice


class AuthenticatorValidateStageTests(TestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = User.objects.get(username="akadmin")
        self.request_factory = RequestFactory()

    def test_stage_validation(self):
        """Test serializer validation"""
        self.client.force_login(self.user)
        serializer = AuthenticatorValidateStageSerializer(
            data={"name": "foo", "not_configured_action": NotConfiguredAction.CONFIGURE}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("not_configured_action", serializer.errors)

    def test_device_challenge_totp(self):
        """Test device challenge"""
        request = self.request_factory.get("/")
        totp_device = TOTPDevice.objects.create(
            user=self.user, confirmed=True, digits=6
        )
        self.assertEqual(get_challenge_for_device(request, totp_device), {})
        with self.assertRaises(ValidationError):
            validate_challenge_code("1234", request, self.user)

    def test_device_challenge_webauthn(self):
        """Test webauthn"""
        request = self.request_factory.get("/")
        request.user = self.user
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

        webauthn_device = WebAuthnDevice.objects.create(
            user=self.user,
            public_key="qwerqwerqre",
            credential_id="foobarbaz",
            sign_count=0,
            rp_id="foo",
        )
        challenge = get_challenge_for_device(request, webauthn_device)
        del challenge["challenge"]
        self.assertEqual(
            challenge,
            {
                "allowCredentials": [
                    {
                        "id": "foobarbaz",
                        "transports": ["usb", "nfc", "ble", "internal"],
                        "type": "public-key",
                    }
                ],
                "rpId": "foo",
                "timeout": 60000,
                "userVerification": "discouraged",
            },
        )

        with self.assertRaises(ValidationError):
            validate_challenge_webauthn({}, request, self.user)

    def test_device_challenge_duo(self):
        """Test duo"""
        request = self.request_factory.get("/")
        stage = AuthenticatorDuoStage.objects.create(
            name="test",
            client_id=generate_client_id(),
            client_secret=generate_client_secret(),
            api_hostname="",
        )
        duo_device = DuoDevice.objects.create(
            user=self.user,
            stage=stage,
        )
        duo_mock = MagicMock(
            auth=MagicMock(
                return_value={
                    "result": "allow",
                    "status": "allow",
                    "status_msg": "Success. Logging you in...",
                }
            )
        )
        failed_duo_mock = MagicMock(auth=MagicMock(return_value={"result": "deny"}))
        with patch(
            "authentik.stages.authenticator_duo.models.AuthenticatorDuoStage.client",
            duo_mock,
        ):
            self.assertEqual(
                duo_device.pk, validate_challenge_duo(duo_device.pk, request, self.user)
            )
        with patch(
            "authentik.stages.authenticator_duo.models.AuthenticatorDuoStage.client",
            failed_duo_mock,
        ):
            with self.assertRaises(ValidationError):
                validate_challenge_duo(duo_device.pk, request, self.user)
