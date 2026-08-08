"""bsky key generation and signing tests"""

from base64 import urlsafe_b64encode
from hashlib import sha256

import jwt
from django.http import HttpRequest
from django.test import TestCase
from jwt import PyJWK

from authentik.sources.bsky.keys import (
    generate_bsky_signing_key,
    public_jwk,
    sign_client_assertion,
    sign_dpop_proof,
)
from authentik.sources.bsky.models import BskySource


def _fake_request() -> HttpRequest:
    request = HttpRequest()
    request.META["SERVER_NAME"] = "testserver"
    request.META["SERVER_PORT"] = "80"
    return request


class TestGenerateSigningKey(TestCase):
    """Test generate_bsky_signing_key"""

    def test_generates_valid_pem(self):
        """Test the generated key is a loadable EC P-256 PEM private key"""
        pem = generate_bsky_signing_key()
        self.assertIn("BEGIN PRIVATE KEY", pem)


class TestPublicJwk(TestCase):
    """Test public_jwk"""

    def setUp(self):
        self.source = BskySource.objects.create(name="test", slug="test")

    def test_public_jwk_shape(self):
        """Test public_jwk returns only the RFC 7638 required EC members, no private material"""
        jwk = public_jwk(self.source)
        self.assertEqual(set(jwk.keys()), {"kty", "crv", "x", "y"})


class TestSignClientAssertion(TestCase):
    """Test sign_client_assertion"""

    def setUp(self):
        self.source = BskySource.objects.create(name="test", slug="test")

    def test_client_assertion_claims_and_signature(self):
        """Test the assertion is signed correctly and carries iss/sub/aud/kid"""
        request = _fake_request()
        assertion = sign_client_assertion(self.source, request, "https://authserver.example.com")

        header = jwt.get_unverified_header(assertion)
        self.assertEqual(header["alg"], "ES256")
        self.assertIn("kid", header)

        key = PyJWK.from_dict({**public_jwk(self.source), "kid": header["kid"]})
        payload = jwt.decode(
            assertion,
            key.key,
            algorithms=["ES256"],
            audience="https://authserver.example.com",
        )

        client_id = self.source.client_id(request)
        self.assertEqual(payload["iss"], client_id)
        self.assertEqual(payload["sub"], client_id)
        self.assertEqual(payload["aud"], "https://authserver.example.com")

    def test_client_assertion_expiry(self):
        """Test the assertion has a short (~60s) expiry"""
        request = _fake_request()
        assertion = sign_client_assertion(self.source, request, "https://authserver.example.com")
        payload = jwt.decode(assertion, options={"verify_signature": False})
        self.assertEqual(payload["exp"] - payload["iat"], 60)


class TestSignDpopProof(TestCase):
    """Test sign_dpop_proof"""

    def setUp(self):
        self.source = BskySource.objects.create(name="test", slug="test")

    def test_dpop_proof_round_trips(self):
        """Test a generated proof verifies against its own embedded public jwk"""
        proof = sign_dpop_proof(self.source, "POST", "https://authserver.example.com/oauth/par")
        header = jwt.get_unverified_header(proof)
        self.assertEqual(header["typ"], "dpop+jwt")

        key = PyJWK.from_dict(header["jwk"])
        payload = jwt.decode(proof, key.key, algorithms=["ES256"])
        self.assertEqual(payload["htm"], "POST")
        self.assertEqual(payload["htu"], "https://authserver.example.com/oauth/par")

    def test_dpop_proof_includes_nonce_when_given(self):
        """Test the nonce claim is present only when passed"""
        proof_without = sign_dpop_proof(
            self.source, "POST", "https://authserver.example.com/oauth/par"
        )
        payload_without = jwt.decode(proof_without, options={"verify_signature": False})
        self.assertNotIn("nonce", payload_without)

        proof_with = sign_dpop_proof(
            self.source,
            "POST",
            "https://authserver.example.com/oauth/par",
            nonce="server-nonce",
        )
        payload_with = jwt.decode(proof_with, options={"verify_signature": False})
        self.assertEqual(payload_with["nonce"], "server-nonce")

    def test_dpop_proof_includes_ath_when_access_token_given(self):
        """Test the ath claim is base64url(sha256(access_token)) when presenting a token"""
        access_token = "example-access-token"
        proof = sign_dpop_proof(
            self.source,
            "GET",
            "https://pds.example.com/xrpc/some.method",
            access_token=access_token,
        )
        payload = jwt.decode(proof, options={"verify_signature": False})
        expected_ath = (
            urlsafe_b64encode(sha256(access_token.encode()).digest()).rstrip(b"=").decode()
        )
        self.assertEqual(payload["ath"], expected_ath)

        proof_without_token = sign_dpop_proof(
            self.source, "GET", "https://pds.example.com/xrpc/some.method"
        )
        payload_without_token = jwt.decode(proof_without_token, options={"verify_signature": False})
        self.assertNotIn("ath", payload_without_token)
