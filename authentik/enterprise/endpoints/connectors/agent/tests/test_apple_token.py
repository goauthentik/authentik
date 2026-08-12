from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.test import TestCase
from django.urls import reverse
from jwt import encode

from authentik.blueprints.tests import apply_blueprint, reconcile_app
from authentik.core.tests.utils import create_test_cert, create_test_user
from authentik.crypto.builder import PrivateKeyAlg
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    AgentDeviceUserBinding,
    AppleIndependentSecureEnclave,
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
        self.sign_key_pem = self.apple_sign_key.public_key.public_bytes(
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
            apple_signing_key=self.sign_key_pem,
            apple_encryption_key=self.enc_pub,
        )
        self.user = create_test_user()
        AgentDeviceUserBinding.objects.create(
            target=self.device,
            user=self.user,
            order=0,
            apple_enclave_key_id=self.apple_sign_key.kid,
            apple_secure_enclave_key=self.sign_key_pem,
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

    def _password_request(self, nonce: str, **claims) -> str:
        """Build the login request macOS sends for a Platform SSO password login: the
        credential travels as claims of the signed request, and the grant_type that
        identifies it is a claim rather than the jwt-bearer sent in the form."""
        return encode(
            {
                "iss": str(self.connector.pk),
                "aud": "http://testserver/endpoints/agent/psso/token/",
                "request_nonce": nonce,
                "grant_type": "password",
                "amr": ["pwd"],
                "username": self.user.username,
                "jwe_crypto": {
                    "apv": (
                        "AAAABUFwcGxlAAAAQQTFgZOospN6KbkhXhx1lfa-AKYxjEfJhTJrkpdEY_srMmkPzS7VN0Bzt2AtNBEXE"
                        "aphDONiP2Mq6Oxytv5JKOxHAAAAJDgyOThERkY5LTVFMUUtNEUwMS04OEUwLUI3QkQzOUM4QjA3Qw"
                    )
                },
                **claims,
            },
            self.apple_sign_key.private_key,
            headers={"kid": self.apple_sign_key.kid},
            algorithm=JWTAlgorithms.from_private_key(self.apple_sign_key.private_key),
        )

    def _post_password_request(self, assertion: str):
        return self.client.post(
            reverse("authentik_enterprise_endpoints_connectors_agent:psso-token"),
            data={
                "assertion": assertion,
                "platform_sso_version": "1.0",
                # macOS posts every Platform SSO login as jwt-bearer, password ones too
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            },
        )

    @apply_blueprint("default/flow-endpoints-agent-psso-password.yaml")
    @reconcile_app("authentik_crypto")
    def test_token_password(self):
        """A password login authenticates against the dedicated flow's password stage"""
        password = generate_id()
        self.user.set_password(password)
        self.user.save()
        nonce = generate_id()
        AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)

        res = self._post_password_request(self._password_request(nonce, password=password))

        self.assertEqual(res.status_code, 200)
        event = Event.objects.filter(
            action=EventAction.LOGIN,
            app="authentik.endpoints.connectors.agent",
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context["device"]["name"], self.device.name)

    @apply_blueprint("default/flow-endpoints-agent-psso-password.yaml")
    @reconcile_app("authentik_crypto")
    def test_token_password_invalid(self):
        """A wrong password is rejected as an invalid credential and issues no token"""
        self.user.set_password(generate_id())
        self.user.save()
        nonce = generate_id()
        AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)

        res = self._post_password_request(self._password_request(nonce, password=generate_id()))

        # 401 with this body, not a 400: it is what macOS reads as "wrong password" and
        # re-prompts for, rather than failing the login outright.
        self.assertEqual(res.status_code, 401)
        self.assertJSONEqual(res.content, {"error": "invalid_grant"})
        self.assertFalse(
            Event.objects.filter(
                action=EventAction.LOGIN,
                app="authentik.endpoints.connectors.agent",
            ).exists()
        )

    @apply_blueprint("default/flow-endpoints-agent-psso-password.yaml")
    @reconcile_app("authentik_crypto")
    def test_token_password_unknown_user(self):
        """An unknown username is rejected the same way a bad password is, so that the
        unauthenticated token endpoint cannot be used to enumerate usernames"""
        nonce = generate_id()
        AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)

        res = self._post_password_request(
            self._password_request(nonce, username=generate_id(), password=generate_id())
        )

        self.assertEqual(res.status_code, 401)
        self.assertJSONEqual(res.content, {"error": "invalid_grant"})

    @reconcile_app("authentik_crypto")
    def test_token_unknown_kid(self):
        """An assertion signed by a key ID we don't know must be rejected with a 400"""
        assertion = encode(
            {
                "iss": str(self.connector.pk),
                "aud": "http://testserver/endpoints/agent/psso/token/",
                "request_nonce": generate_id(),
            },
            self.apple_sign_key.private_key,
            headers={
                "kid": generate_id(),
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
        self.assertEqual(res.status_code, 400)

    @reconcile_app("authentik_crypto")
    def test_token_unregistered_enclave(self):
        """A device with no Secure Enclave key registered must be rejected with a 400"""
        AgentDeviceUserBinding.objects.all().update(apple_enclave_key_id="")
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
        self.assertEqual(res.status_code, 400)

    @reconcile_app("authentik_crypto")
    def test_token_independent(self):
        nonce = generate_id()

        AgentDeviceUserBinding.objects.all().delete()
        AppleIndependentSecureEnclave.objects.create(
            user=self.user,
            apple_enclave_key_id=self.apple_sign_key.kid,
            apple_secure_enclave_key=self.sign_key_pem,
        )

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
