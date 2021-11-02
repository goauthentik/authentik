"""Test validator stage"""
from unittest.mock import MagicMock, patch

from django.test.client import RequestFactory
from django.urls.base import reverse
from django.utils.encoding import force_str
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase
from webauthn.helpers import bytes_to_base64url

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.models import Flow, FlowStageBinding, NotConfiguredAction
from authentik.lib.generators import generate_id, generate_key
from authentik.lib.tests.utils import get_request
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.api import AuthenticatorValidateStageSerializer
from authentik.stages.authenticator_validate.challenge import (
    get_challenge_for_device,
    validate_challenge_code,
    validate_challenge_duo,
    validate_challenge_webauthn,
)
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
from authentik.stages.identification.models import IdentificationStage, UserFields


class AuthenticatorValidateStageTests(APITestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = User.objects.get(username="akadmin")
        self.request_factory = RequestFactory()

    def test_not_configured_action(self):
        """Test not_configured_action"""
        conf_stage = IdentificationStage.objects.create(
            name="conf",
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            configuration_stage=conf_stage,
        )
        flow = Flow.objects.create(name="test", slug="test", title="test")
        FlowStageBinding.objects.create(target=flow, stage=conf_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": "akadmin"},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "type": ChallengeTypes.NATIVE.value,
                "component": "ak-stage-identification",
                "password_fields": False,
                "primary_action": "Log in",
                "flow_info": {
                    "background": flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": flow.title,
                },
                "user_fields": ["username"],
                "sources": [],
                "show_source_labels": False,
            },
        )

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
        totp_device = TOTPDevice.objects.create(user=self.user, confirmed=True, digits=6)
        self.assertEqual(get_challenge_for_device(request, totp_device), {})
        with self.assertRaises(ValidationError):
            validate_challenge_code("1234", request, self.user)

    def test_device_challenge_webauthn(self):
        """Test webauthn"""
        request = get_request("/")
        request.user = self.user

        webauthn_device = WebAuthnDevice.objects.create(
            user=self.user,
            public_key=bytes_to_base64url(b"qwerqwerqre"),
            credential_id=bytes_to_base64url(b"foobarbaz"),
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
                        "id": "Zm9vYmFyYmF6",
                        "type": "public-key",
                    }
                ],
                "rpId": "testserver",
                "timeout": 60000,
                "userVerification": "preferred",
            },
        )

        with self.assertRaises(ValidationError):
            validate_challenge_webauthn({}, request, self.user)

    def test_device_challenge_duo(self):
        """Test duo"""
        request = self.request_factory.get("/")
        stage = AuthenticatorDuoStage.objects.create(
            name="test",
            client_id=generate_id(),
            client_secret=generate_key(),
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
