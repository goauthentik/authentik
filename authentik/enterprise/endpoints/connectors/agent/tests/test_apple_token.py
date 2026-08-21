from base64 import b64decode, b64encode
from json import loads

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import GCM
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_private_key,
)
from django.test import TestCase
from django.urls import reverse
from jwcrypto.common import base64url_decode
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
    AppleUserKey,
    DeviceAuthenticationToken,
    DeviceToken,
    EnrollmentToken,
)
from authentik.endpoints.models import Device
from authentik.enterprise.endpoints.connectors.agent.http import length_prefixed
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

    APV = (
        "AAAABUFwcGxlAAAAQQTFgZOospN6KbkhXhx1lfa-AKYxjEfJhTJrkpdEY_srMmkPzS7VN0Bzt2AtNBEXE"
        "aphDONiP2Mq6Oxytv5JKOxHAAAAJDgyOThERkY5LTVFMUUtNEUwMS04OEUwLUI3QkQzOUM4QjA3Qw"
    )

    def _decrypt_key_response(self, content: bytes) -> bytes:
        """Decrypt a key response the way macOS would, and return the raw `key` it carries.

        Mirrors encrypt_token_with_a256_gcm: ECDH against the ephemeral key in the header,
        Concat KDF over the same OtherInfo, then AES-GCM with the protected header as AAD.
        Doing it the long way here is deliberate -- it proves the response the Mac receives
        decrypts to the secret it derives independently, which a round-trip through our own
        encrypt helper would not."""
        protected_b64, _, iv_b64, ciphertext_b64, tag_b64 = content.decode().split(".")
        header = loads(base64url_decode(protected_b64))
        ephemeral_public = ec.EllipticCurvePublicNumbers(
            x=int.from_bytes(base64url_decode(header["epk"]["x"]), "big"),
            y=int.from_bytes(base64url_decode(header["epk"]["y"]), "big"),
            curve=ec.SECP256R1(),
        ).public_key()
        shared_secret = self.enc_key.exchange(ec.ECDH(), ephemeral_public)
        other_info = (
            length_prefixed(b"A256GCM")
            + length_prefixed(base64url_decode(header["apu"]))
            + length_prefixed(base64url_decode(header["apv"]))
            + (256).to_bytes(4, "big")
        )
        derived_key = ConcatKDFHash(
            algorithm=hashes.SHA256(), length=32, otherinfo=other_info
        ).derive(shared_secret)
        decryptor = Cipher(
            AES(derived_key), GCM(base64url_decode(iv_b64), base64url_decode(tag_b64))
        ).decryptor()
        decryptor.authenticate_additional_data(protected_b64.encode())
        plaintext = decryptor.update(base64url_decode(ciphertext_b64)) + decryptor.finalize()
        return b64decode(loads(plaintext)["key"])

    def _key_request(self, nonce: str, **claims) -> str:
        """Build a Platform SSO 2.0 key request. Deliberately carries no aud claim: macOS
        omits it, so requiring one would reject every key request."""
        body = {
            "iss": str(self.connector.pk),
            "request_nonce": nonce,
            "version": "1.0",
            "request_type": "key_request",
            "key_purpose": "user_unlock",
            "username": self.user.username,
            "sub": self.user.username,
            "jwe_crypto": {"alg": "ECDH-ES", "enc": "A256GCM", "apv": self.APV},
        }
        body.update(claims)
        return encode(
            body,
            self.apple_sign_key.private_key,
            headers={"kid": self.apple_sign_key.kid, "typ": "platformsso-key-request+jwt"},
            algorithm=JWTAlgorithms.from_private_key(self.apple_sign_key.private_key),
        )

    def _post_key_request(self, assertion: str):
        return self.client.post(
            reverse("authentik_enterprise_endpoints_connectors_agent:psso-token"),
            data={
                "assertion": assertion,
                "platform_sso_version": "2.0",
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            },
        )

    def _refresh_token(self) -> str:
        return DeviceAuthenticationToken.objects.create(
            device=self.device,
            connector=self.connector,
            user=self.user,
            device_token=self.device_token,
            token=generate_id(),
        ).token

    @reconcile_app("authentik_crypto")
    def test_key_request_provisions_key(self):
        """A key request mints an EC key for the user and returns its certificate."""
        nonce = generate_id()
        AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)

        res = self._post_key_request(self._key_request(nonce, refresh_token=self._refresh_token()))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "application/platformsso-key-response+jwt")
        key = AppleUserKey.objects.filter(
            device_connection=self.connection, username=self.user.username
        ).first()
        self.assertIsNotNone(key)
        self.assertEqual(key.key_purpose, "user_unlock")

    @reconcile_app("authentik_crypto")
    def test_key_request_is_idempotent(self):
        """Re-provisioning on a repeat request would invalidate the key bag the previous
        key unlocked, so the same key must come back."""
        for _ in range(2):
            nonce = generate_id()
            AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)
            res = self._post_key_request(
                self._key_request(nonce, refresh_token=self._refresh_token())
            )
            self.assertEqual(res.status_code, 200)
        self.assertEqual(
            AppleUserKey.objects.filter(
                device_connection=self.connection, username=self.user.username
            ).count(),
            1,
        )

    @reconcile_app("authentik_crypto")
    def test_key_request_without_refresh_token(self):
        """The refresh token is what authorises minting a key, so a request without one is
        refused rather than provisioning against an unauthenticated caller."""
        nonce = generate_id()
        AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)

        res = self._post_key_request(self._key_request(nonce))

        self.assertEqual(res.status_code, 400)
        self.assertFalse(AppleUserKey.objects.exists())

    @reconcile_app("authentik_crypto")
    def test_key_request_with_foreign_refresh_token(self):
        """A refresh token issued for another device must not provision a key here."""
        other_device = Device.objects.create(name=generate_id(), identifier=generate_id())
        other_connection = AgentDeviceConnection.objects.create(
            device=other_device,
            connector=self.connector,
            apple_sign_key_id=generate_id(),
            apple_signing_key=self.sign_key_pem,
            apple_encryption_key=self.enc_pub,
        )
        foreign = DeviceAuthenticationToken.objects.create(
            device=other_device,
            connector=self.connector,
            user=self.user,
            device_token=DeviceToken.objects.create(device=other_connection),
            # A real token value, so this exercises the device check rather than the
            # missing-token path the previous test already covers.
            token=generate_id(),
        )
        nonce = generate_id()
        AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)

        res = self._post_key_request(self._key_request(nonce, refresh_token=foreign.token))

        self.assertEqual(res.status_code, 400)
        self.assertFalse(AppleUserKey.objects.exists())

    @reconcile_app("authentik_crypto")
    def test_key_exchange_returns_shared_secret(self):
        """The exchange must return the same secret the Mac derives on its side."""
        nonce = generate_id()
        AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)
        self._post_key_request(self._key_request(nonce, refresh_token=self._refresh_token()))
        key = AppleUserKey.objects.get(
            device_connection=self.connection, username=self.user.username
        )

        peer = ec.generate_private_key(ec.SECP256R1())
        peer_point = peer.public_key().public_bytes(
            encoding=Encoding.X962, format=PublicFormat.UncompressedPoint
        )
        nonce = generate_id()
        AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)

        res = self._post_key_request(
            self._key_request(
                nonce,
                request_type="key_exchange",
                refresh_token=self._refresh_token(),
                other_publickey=b64encode(peer_point).decode(),
            )
        )

        self.assertEqual(res.status_code, 200)
        server_public = load_pem_private_key(key.private_key.encode(), password=None).public_key()
        self.assertEqual(
            peer.exchange(ec.ECDH(), server_public),
            self._decrypt_key_response(res.content),
        )

    @reconcile_app("authentik_crypto")
    def test_key_exchange_without_provisioned_key(self):
        nonce = generate_id()
        AppleNonce.objects.create(device_token=self.device_token, nonce=nonce)

        res = self._post_key_request(
            self._key_request(
                nonce,
                request_type="key_exchange",
                refresh_token=self._refresh_token(),
                other_publickey=b64encode(b"\x04" + b"\x00" * 64).decode(),
            )
        )

        self.assertEqual(res.status_code, 400)

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
