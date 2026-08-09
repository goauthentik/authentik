from base64 import urlsafe_b64decode

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.test import TestCase
from jwcrypto.jwe import JWE
from jwcrypto.jwk import JWK

from authentik.enterprise.endpoints.connectors.agent.http import (
    base64url_decode,
    encrypt_token_with_a256_gcm,
)


class TestAppleJWE(TestCase):

    def test_encrypt(self):
        data = {"foo": "bar"}
        apv = (
            "AAAABUFwcGxlAAAAQQTFgZOospN6KbkhXhx1lfa-AKYxjEfJhTJrkpdEY_srMmkPzS7VN0Bzt2AtNBEXE"
            "aphDONiP2Mq6Oxytv5JKOxHAAAAJDgyOThERkY5LTVFMUUtNEUwMS04OEUwLUI3QkQzOUM4QjA3Qw"
        )
        key = ec.generate_private_key(curve=ec.SECP256R1())
        pub = (
            key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
        )
        res = encrypt_token_with_a256_gcm(data, pub, base64url_decode(apv))
        parsed = JWE()
        parsed.deserialize(res, JWK.from_pyca(key))
        payload = parsed.payload
        self.assertEqual(payload, b'{"foo": "bar"}')
        self.assertEqual(parsed.jose_header["apv"], apv)
        self.assertEqual(parsed.jose_header["typ"], "platformsso-login-response+jwt")
        self.assertIn(b"APPLE", urlsafe_b64decode(parsed.jose_header["apu"]))
