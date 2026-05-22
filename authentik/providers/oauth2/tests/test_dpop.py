"""Test DPoP validation utilities"""

import base64
import hashlib
import json
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ec import (
    SECP256R1,
    EllipticCurvePrivateKey,
    generate_private_key,
)
from django.core.cache import cache
from django.test import TestCase
from jwt import encode as jwt_encode

from authentik.providers.oauth2.dpop import (
    DPoPError,
    DPoPValidator,
    code_sha256,
    jwk_thumbprint,
)


class DPoPProofBuilder:
    """Helper to build DPoP proof JWTs for testing"""

    def __init__(self, private_key: EllipticCurvePrivateKey | None = None):
        if private_key is None:
            private_key = generate_private_key(SECP256R1())
        self.private_key = private_key
        self.public_key = private_key.public_key()
        nums = self.public_key.public_numbers()
        self.x = (
            base64.urlsafe_b64encode(nums.x.to_bytes(32, "big"))
            .rstrip(b"=")
            .decode()
        )
        self.y = (
            base64.urlsafe_b64encode(nums.y.to_bytes(32, "big"))
            .rstrip(b"=")
            .decode()
        )
        self.jwk = {"kty": "EC", "crv": "P-256", "x": self.x, "y": self.y}

    def build(
        self,
        htm: str = "POST",
        htu: str = "https://server.example.com/token",
        c_s256: str | None = None,
        iat: int | None = None,
        jti: str = "test-jti-001",
        alg: str = "ES256",
        typ: str = "dpop+jwt",
        include_private: bool = False,
    ) -> str:
        headers = {"typ": typ, "jwk": self.jwk.copy(), "alg": alg}
        if include_private:
            # Add a fake private key component to test rejection
            headers["jwk"]["d"] = "fake-private-key"

        payload = {
            "htm": htm,
            "htu": htu,
            "iat": iat if iat is not None else int(time.time()),
            "jti": jti,
        }
        if c_s256 is not None:
            payload["c_s256"] = c_s256

        return jwt_encode(payload, self.private_key, algorithm=alg, headers=headers)

    def make_header(self, htu: str, c_s256: str | None = None) -> str:
        """Build a DPoP proof header for the given token endpoint"""
        return self.build(htm="POST", htu=htu, c_s256=c_s256)

    @property
    def jkt(self) -> str:
        return jwk_thumbprint(self.jwk)


def _craft_jwt(payload: dict, private_key, algorithm: str, headers: dict) -> str:
    """Craft a JWT manually, bypassing PyJWT's algorithm validation.

    This allows creating JWTs where the header claims a different algorithm
    than what was used to sign, for testing rejection of such proofs.
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, padding

    header_bytes = json.dumps(headers, separators=(",", ":")).encode()
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    segments = [
        base64.urlsafe_b64encode(header_bytes).rstrip(b"="),
        base64.urlsafe_b64encode(payload_bytes).rstrip(b"="),
    ]
    signing_input = b".".join(segments)

    if algorithm == "ES256":
        signature = private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    elif algorithm == "ES384":
        signature = private_key.sign(signing_input, ec.ECDSA(hashes.SHA384()))
    elif algorithm == "ES512":
        signature = private_key.sign(signing_input, ec.ECDSA(hashes.SHA512()))
    elif algorithm in ("RS256", "PS256"):
        signature = private_key.sign(
            signing_input,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            )
            if algorithm.startswith("PS")
            else padding.PKCS1v15(),
            hashes.SHA256(),
        )
    else:
        raise ValueError(f"Unsupported test algorithm: {algorithm}")

    segments.append(base64.urlsafe_b64encode(signature).rstrip(b"="))
    return b".".join(segments).decode()
    """Test JWK thumbprint computation"""

    def test_ec_thumbprint(self):
        """Test EC P-256 thumbprint computation."""
        builder = DPoPProofBuilder()
        thumbprint = jwk_thumbprint(builder.jwk)
        self.assertIsInstance(thumbprint, str)
        self.assertGreater(len(thumbprint), 0)
        # Verify consistency
        self.assertEqual(thumbprint, jwk_thumbprint(builder.jwk))

    def test_rsa_thumbprint(self):
        """Test RSA thumbprint computation."""
        from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

        private_key = generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        n = (
            base64.urlsafe_b64encode(public_key.public_numbers().n.to_bytes(256, "big"))
            .rstrip(b"=")
            .decode()
        )
        e = (
            base64.urlsafe_b64encode(public_key.public_numbers().e.to_bytes(3, "big"))
            .rstrip(b"=")
            .decode()
        )
        jwk = {"kty": "RSA", "n": n, "e": e}
        thumbprint = jwk_thumbprint(jwk)
        self.assertIsInstance(thumbprint, str)
        self.assertGreater(len(thumbprint), 0)

    def test_unsupported_kty(self):
        """Test unsupported key type — jwcrypto may accept it but DPoP validator rejects it"""
        validator = DPoPValidator()
        with self.assertRaises(DPoPError):
            validator._validate_jwk({"kty": "oct", "k": "foo"})


class TestComputeCS256(TestCase):
    """Test c_s256 computation"""

    def test_code_sha256(self):
        """Test c_s256 matches expected BASE64URL(SHA256(ASCII(value)))"""
        value = "SplxlOBeZQQYbYS6WxSbIA"
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(value.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertEqual(code_sha256(value), expected)

    def test_code_sha256_empty(self):
        """Test c_s256 with empty string"""
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(b"").digest()
        ).rstrip(b"=").decode("ascii")
        self.assertEqual(code_sha256(""), expected)


class TestDPoPValidator(TestCase):
    """Test DPoP proof validation."""

    def setUp(self):
        self.validator = DPoPValidator()
        self.builder = DPoPProofBuilder()
        self.htu = "https://server.example.com/token"
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_valid_proof(self):
        """Test a completely valid DPoP proof"""
        c_s256 = code_sha256("test-code")
        proof = self.builder.build(c_s256=c_s256)
        result = self.validator.validate(
            proof, expected_htm="POST", expected_htu=self.htu, expected_jkt=self.builder.jkt, expected_c_s256=c_s256
        )
        self.assertEqual(result["kty"], "EC")
        self.assertEqual(result["crv"], "P-256")

    def test_valid_proof_without_expected_jkt(self):
        """Test valid proof without expected_jkt check"""
        proof = self.builder.build(htu=self.htu)
        result = self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertEqual(result["kty"], "EC")

    def test_invalid_signature(self):
        """Test proof signed with different key than embedded jwk"""
        other_builder = DPoPProofBuilder()
        # Sign with other key but embed original jwk
        payload = {
            "htm": "POST",
            "htu": self.htu,
            "iat": int(time.time()),
            "jti": "test-jti-002",
        }
        proof = jwt_encode(
            payload,
            other_builder.private_key,
            algorithm="ES256",
            headers={"typ": "dpop+jwt", "jwk": self.builder.jwk},
        )
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("signature", str(cm.exception).lower())

    def test_missing_typ_header(self):
        """Test rejection when typ header is not dpop+jwt"""
        proof = self.builder.build(typ="jwt")
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("typ", str(cm.exception).lower())

    def test_private_key_material(self):
        """Test rejection when jwk contains private key material"""
        proof = self.builder.build(include_private=True)
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("private", str(cm.exception).lower())

    def test_htm_mismatch(self):
        """Test rejection when htm doesn't match"""
        proof = self.builder.build(htm="GET", htu=self.htu)
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("htm", str(cm.exception).lower())

    def test_htu_mismatch(self):
        """Test rejection when htu doesn't match"""
        proof = self.builder.build(htu="https://other.example.com/token")
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("htu", str(cm.exception).lower())

    def test_htu_ignores_query_and_fragment(self):
        """Test htu matching ignores query and fragment"""
        proof = self.builder.build(htu=self.htu + "?foo=bar#baz")
        result = self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertEqual(result["kty"], "EC")

    def test_expired_iat(self):
        """Test rejection when iat is too old"""
        proof = self.builder.build(htu=self.htu, iat=int(time.time()) - 120)
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("iat", str(cm.exception).lower())

    def test_future_iat(self):
        """Test rejection when iat is in the future"""
        proof = self.builder.build(htu=self.htu, iat=int(time.time()) + 120)
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("iat", str(cm.exception).lower())

    def test_missing_jti(self):
        """Test rejection when jti is missing"""
        proof = self.builder.build(htu=self.htu, jti="")
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("jti", str(cm.exception).lower())

    def test_expected_jkt_mismatch(self):
        """Test rejection when JWK thumbprint doesn't match expected_jkt"""
        other_builder = DPoPProofBuilder()
        proof = other_builder.build(htu=self.htu)
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(
                proof, expected_htm="POST", expected_htu=self.htu, expected_jkt=self.builder.jkt
            )
        self.assertIn("thumbprint", str(cm.exception).lower())

    def test_expected_jkt_match(self):
        """Test acceptance when JWK thumbprint matches expected_jkt"""
        proof = self.builder.build(htu=self.htu)
        result = self.validator.validate(
            proof, expected_htm="POST", expected_htu=self.htu, expected_jkt=self.builder.jkt
        )
        self.assertEqual(result["kty"], "EC")

    def test_c_s256_mismatch(self):
        """Test rejection when c_s256 doesn't match"""
        proof = self.builder.build(c_s256="wrong-hash")
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(
                proof, expected_htm="POST", expected_htu=self.htu, expected_c_s256=code_sha256("correct-code")
            )
        self.assertIn("c_s256", str(cm.exception).lower())

    def test_c_s256_match(self):
        """Test acceptance when c_s256 matches"""
        code = "test-auth-code-123"
        c_s256 = code_sha256(code)
        proof = self.builder.build(c_s256=c_s256)
        result = self.validator.validate(
            proof, expected_htm="POST", expected_htu=self.htu, expected_c_s256=c_s256
        )
        self.assertEqual(result["kty"], "EC")

    def test_c_s256_missing_when_required(self):
        """Test rejection when c_s256 param provided but claim absent"""
        proof = self.builder.build(htu=self.htu)
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(
                proof, expected_htm="POST", expected_htu=self.htu, expected_c_s256=code_sha256("some-code")
            )
        self.assertIn("c_s256", str(cm.exception).lower())

    def test_symmetric_key_rejected(self):
        """Test rejection of symmetric keys"""
        payload = {
            "htm": "POST",
            "htu": self.htu,
            "iat": int(time.time()),
            "jti": "test-jti-003",
        }

        with self.assertRaises(DPoPError) as cm:
            self.validator._validate_jwk({"kty": "oct", "k": "foo"})
        self.assertIn("Unsupported", str(cm.exception))

    def test_invalid_jwt(self):
        """Test rejection of malformed JWT"""
        with self.assertRaises(DPoPError):
            self.validator.validate("not-a-jwt", expected_htm="POST", expected_htu=self.htu)

    def test_missing_jwk(self):
        """Test rejection when jwk is missing from header"""
        payload = {
            "htm": "POST",
            "htu": self.htu,
            "iat": int(time.time()),
            "jti": "test-jti-004",
        }
        proof = jwt_encode(
            payload,
            self.builder.private_key,
            algorithm="ES256",
            headers={"typ": "dpop+jwt"},
        )
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("jwk", str(cm.exception).lower())

    def test_jti_replay_rejected(self):
        """Test that reusing the same jti is rejected"""
        jti = "unique-jti-12345"
        proof = self.builder.build(htu=self.htu, jti=jti)
        # First use should succeed
        self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        # Second use with same jti should fail
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("replay", str(cm.exception).lower())

    def test_jti_different_accepted(self):
        """Test that different jti values are both accepted"""
        proof1 = self.builder.build(htu=self.htu, jti="jti-first")
        proof2 = self.builder.build(htu=self.htu, jti="jti-second")
        self.validator.validate(proof1, expected_htm="POST", expected_htu=self.htu)
        self.validator.validate(proof2, expected_htm="POST", expected_htu=self.htu)

    def test_jti_too_large(self):
        """Test rejection when jti exceeds maximum length"""
        large_jti = "x" * 257
        proof = self.builder.build(htu=self.htu, jti=large_jti)
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("too large", str(cm.exception).lower())

    def test_symmetric_alg_rejected(self):
        """Test rejection when alg header claims a symmetric algorithm"""
        payload = {
            "htm": "POST",
            "htu": self.htu,
            "iat": int(time.time()),
            "jti": "test-jti-sym",
        }
        # Craft a JWT with HS256 in the header but signed with EC key
        proof = _craft_jwt(
            payload,
            self.builder.private_key,
            algorithm="ES256",
            headers={"typ": "dpop+jwt", "jwk": self.builder.jwk, "alg": "HS256"},
        )
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("algorithm", str(cm.exception).lower())

    def test_alg_jwk_mismatch_rejected(self):
        """Test rejection when alg doesn't match JWK key type"""
        payload = {
            "htm": "POST",
            "htu": self.htu,
            "iat": int(time.time()),
            "jti": "test-jti-mismatch",
        }
        # Craft a JWT with RS256 in the header but EC jwk and signature
        proof = _craft_jwt(
            payload,
            self.builder.private_key,
            algorithm="ES256",
            headers={"typ": "dpop+jwt", "jwk": self.builder.jwk, "alg": "RS256"},
        )
        with self.assertRaises(DPoPError) as cm:
            self.validator.validate(proof, expected_htm="POST", expected_htu=self.htu)
        self.assertIn("signature", str(cm.exception).lower())
