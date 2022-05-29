"""Test validator stage"""
from time import sleep

from django.test.client import RequestFactory
from django.urls.base import reverse
from rest_framework.exceptions import ValidationError
from webauthn.helpers import bytes_to_base64url

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow, FlowStageBinding, NotConfiguredAction
from authentik.flows.tests import FlowTestCase
from authentik.lib.tests.utils import get_request
from authentik.stages.authenticator_validate.challenge import (
    get_challenge_for_device,
    validate_challenge_webauthn,
)
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
from authentik.stages.identification.models import IdentificationStage, UserFields


class AuthenticatorValidateStageWebAuthnTests(FlowTestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()

    def test_last_auth_threshold(self):
        """Test last_auth_threshold"""
        ident_stage = IdentificationStage.objects.create(
            name="conf",
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: WebAuthnDevice = WebAuthnDevice.objects.create(
            user=self.user,
            confirmed=True,
        )
        device.set_sign_count(device.sign_count + 1)
        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            last_auth_threshold="milliseconds=0",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.WEBAUTHN],
        )
        sleep(1)
        stage.configuration_stages.set([ident_stage])
        flow = Flow.objects.create(name="test", slug="test", title="test")
        FlowStageBinding.objects.create(target=flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            follow=True,
        )
        self.assertStageResponse(
            response,
            flow,
            component="ak-stage-authenticator-validate",
        )

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
