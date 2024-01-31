"""Test WebAuthn API"""

from base64 import b64decode

from django.urls import reverse
from webauthn.helpers.bytes_to_base64url import bytes_to_base64url

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_webauthn.models import AuthenticateWebAuthnStage, WebAuthnDevice
from authentik.stages.authenticator_webauthn.stage import SESSION_KEY_WEBAUTHN_CHALLENGE


class TestAuthenticatorWebAuthnStage(FlowTestCase):
    """Test WebAuthn API"""

    def setUp(self) -> None:
        self.stage = AuthenticateWebAuthnStage.objects.create(
            name=generate_id(),
        )
        self.flow = create_test_flow()
        self.binding = FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )
        self.user = create_test_admin_user()

    def test_api_delete(self):
        """Test api delete"""
        self.client.force_login(self.user)
        dev = WebAuthnDevice.objects.create(user=self.user)
        response = self.client.delete(
            reverse("authentik_api:webauthndevice-detail", kwargs={"pk": dev.pk})
        )
        self.assertEqual(response.status_code, 204)

    def test_registration_options(self):
        """Test registration options"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session[SESSION_KEY_WEBAUTHN_CHALLENGE] = b64decode(
            (
                "o90Yh1osqW3mjGift+6WclWOya5lcdff/G0mqueN3hChacMUz"
                "V4mxiDafuQ0x0e1d/fcPai0fx/jMBZ8/nG2qQ=="
            ).encode()
        )
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            registration={
                "rp": {"name": "authentik", "id": "testserver"},
                "user": {
                    "id": bytes_to_base64url(self.user.uid.encode("utf-8")),
                    "name": self.user.username,
                    "displayName": self.user.name,
                },
                "challenge": bytes_to_base64url(session[SESSION_KEY_WEBAUTHN_CHALLENGE]),
                "pubKeyCredParams": [
                    {"type": "public-key", "alg": -7},
                    {"type": "public-key", "alg": -8},
                    {"type": "public-key", "alg": -36},
                    {"type": "public-key", "alg": -37},
                    {"type": "public-key", "alg": -38},
                    {"type": "public-key", "alg": -39},
                    {"type": "public-key", "alg": -257},
                    {"type": "public-key", "alg": -258},
                    {"type": "public-key", "alg": -259},
                ],
                "timeout": 60000,
                "excludeCredentials": [],
                "authenticatorSelection": {
                    "residentKey": "preferred",
                    "requireResidentKey": False,
                    "userVerification": "preferred",
                },
                "attestation": "none",
            },
        )
