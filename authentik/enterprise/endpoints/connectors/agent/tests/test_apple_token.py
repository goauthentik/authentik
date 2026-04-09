from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.test import TestCase
from django.urls import reverse
from jwt import encode

from authentik.blueprints.tests import reconcile_app
from authentik.core.tests.utils import create_test_cert, create_test_user
from authentik.crypto.builder import PrivateKeyAlg
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    AgentDeviceUserBinding,
    AppleNonce,
    DeviceToken,
    EnrollmentToken,
)
from authentik.endpoints.models import Device
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import JWTAlgorithms


class TestAppleToken(TestCase):

    def setUp(self):
        self.apple_sign_key = create_test_cert(PrivateKeyAlg.ECDSA)
        sign_key_pem = self.apple_sign_key.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        self.enc_key = ec.generate_private_key(curve=ec.SECP256R1())
        self.enc_pub = (
            self.enc_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
        )

        self.connector = AgentConnector.objects.create(name=generate_id())
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.device = Device.objects.create(
            name=generate_id(),
            identifier=generate_id(),
        )
        self.connection = AgentDeviceConnection.objects.create(
            device=self.device,
            connector=self.connector,
            apple_sign_key_id=self.apple_sign_key.kid,
            apple_signing_key=sign_key_pem,
            apple_encryption_key=self.enc_pub,
        )
        self.user = create_test_user()
        AgentDeviceUserBinding.objects.create(
            target=self.device,
            user=self.user,
            order=0,
            apple_enclave_key_id=self.apple_sign_key.kid,
            apple_secure_enclave_key=sign_key_pem,
        )
        self.device_token = DeviceToken.objects.create(device=self.connection)

    @reconcile_app("authentik_crypto")
    def test_token(self):
        nonce = generate_id()
        AppleNonce.objects.create(
            device_token=self.device_token,
            nonce=nonce,
        )
        embedded = encode(
            {"iss": str(self.connector.pk), "aud": str(self.device.pk), "request_nonce": nonce},
            self.apple_sign_key.private_key,
            headers={
                "kid": self.apple_sign_key.kid,
            },
            algorithm=JWTAlgorithms.from_private_key(self.apple_sign_key.private_key),
        )
        assertion = encode(
            {
                "iss": str(self.connector.pk),
                "aud": "http://testserver/endpoints/agent/psso/token/",
                "request_nonce": nonce,
                "assertion": embedded,
                "jwe_crypto": {
                    "apv": (
                        "AAAABUFwcGxlAAAAQQTFgZOospN6KbkhXhx1lfa-AKYxjEfJhTJrkpdEY_srMmkPzS7VN0Bzt2AtNBEXE"
                        "aphDONiP2Mq6Oxytv5JKOxHAAAAJDgyOThERkY5LTVFMUUtNEUwMS04OEUwLUI3QkQzOUM4QjA3Qw"
                    )
                },
            },
            self.apple_sign_key.private_key,
            headers={
                "kid": self.apple_sign_key.kid,
            },
            algorithm=JWTAlgorithms.from_private_key(self.apple_sign_key.private_key),
        )
        res = self.client.post(
            reverse("authentik_enterprise_endpoints_connectors_agent:psso-token"),
            data={
                "assertion": assertion,
                "platform_sso_version": "1.0",
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            },
        )

        self.assertEqual(res.status_code, 200)
        event = Event.objects.filter(
            action=EventAction.LOGIN,
            app="authentik.endpoints.connectors.agent",
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["device"]["name"], self.device.name)
