"""DPoP (Demonstrating Proof-of-Possession) utils"""

import base64
import hashlib
import json
import time
from hmac import compare_digest
from typing import Any
from urllib.parse import urlparse

from django.core.cache import cache
from django.db import DatabaseError, transaction
from jwt import PyJWK, decode as jwt_decode
from jwt import decode_complete as jwt_decode_complete
from jwt.exceptions import InvalidTokenError, PyJWTError
from jwcrypto.jwk import JWK
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()

# Clock skew tolerance in seconds for `iat` validation
DPOP_IAT_CLOCK_SKEW = 60

# DPoP JWT type header value
DPOP_JWT_TYPE = "dpop+jwt"

# Supported asymmetric key types for DPoP
DPOP_SUPPORTED_KTYS = {"EC", "RSA"}

# Supported asymmetric signature algorithms for DPoP
DPOP_SUPPORTED_ALGS = {
    "ES256",
    "ES384",
    "ES512",
    "RS256",
    "RS384",
    "RS512",
    "PS256",
    "PS384",
    "PS512",
}

# JTI replay protection window in seconds
DPOP_JTI_REPLAY_WINDOW = int(CONFIG.get("providers.oauth2.dpop_jti_replay_window", 120))

# Maximum allowed JTI length
DPOP_JTI_MAX_LENGTH = 256

# Cache key template for tracked JTIs
CACHE_KEY_DPOP_JTI = "authentik_providers_oauth2_dpop_jti_%s"


def jwk_thumbprint(jwk: dict) -> str:
    """Compute the SHA-256 JWK Thumbprint per RFC 7638"""
    key = JWK.from_json(json.dumps(jwk))
    return key.thumbprint()


def code_sha256(value: str) -> str:
    """Compute c_s256: BASE64URL(SHA256(ASCII(value)))"""
    digest = hashlib.sha256(value.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class DPoPError(Exception):
    """Raised when DPoP proof validation fails"""


class DPoPValidator:
    """Validates DPoP proof JWTs per RFC 9449 Section 5"""

    def validate(
        self,
        dpop_proof: str,
        expected_htm: str,
        expected_htu: str,
        expected_jkt: str | None = None,
        expected_c_s256: str | None = None,
    ) -> dict:
        """Validate a DPoP proof JWT.

        :param dpop_proof: The DPoP proof JWT string
        :param expected_htm: Expected HTTP method (e.g., "POST")
        :param expected_htu: Expected token endpoint URL
        :param expected_jkt: Expected JWK thumbprint (from auth request)
        :param expected_c_s256: Expected c_s256 hash (of code or device_code)
        :return: The validated public key JWK dict
        :raises DPoPError: If validation fails
        """
        try:
            # Extract the protected JOSE header (compact serialization has no unprotected header)
            unverified = jwt_decode_complete(
                dpop_proof,
                options={"verify_signature": False, "verify_exp": False, "verify_iat": False},
            )
            header = unverified.get("header", {})
        except PyJWTError as exc:
            raise DPoPError("Invalid DPoP proof JWT") from exc

        if header.get("typ") != DPOP_JWT_TYPE:
            raise DPoPError(f"Invalid DPoP typ header: {header.get('typ')}")

        jwk = header.get("jwk")
        if not isinstance(jwk, dict):
            raise DPoPError("Missing jwk in DPoP header")

        self._validate_jwk(jwk)

        alg = header.get("alg")
        if not alg:
            raise DPoPError("Missing alg in DPoP header")
        if alg not in DPOP_SUPPORTED_ALGS:
            raise DPoPError(f"Unsupported DPoP algorithm: {alg}")

        try:
            key = PyJWK.from_dict(jwk)
            payload = jwt_decode(
                dpop_proof, key.key, algorithms=[alg],
                options={"verify_iat": False}
            )
        except (PyJWTError, InvalidTokenError) as exc:
            raise DPoPError("DPoP proof signature verification failed") from exc

        if payload.get("htm") != expected_htm:
            raise DPoPError(
                f"DPoP htm mismatch: expected {expected_htm}, got {payload.get('htm')}"
            )

        payload_htu = payload.get("htu")
        if not payload_htu:
            raise DPoPError("DPoP proof missing htu claim")
        if not self._htu_matches(payload_htu, expected_htu):
            raise DPoPError(
                f"DPoP htu mismatch: expected {expected_htu}, got {payload_htu}"
            )

        iat = payload.get("iat")
        if not isinstance(iat, int):
            raise DPoPError("DPoP proof missing or invalid iat claim")
        now = int(time.time())
        if abs(now - iat) > DPOP_IAT_CLOCK_SKEW:
            raise DPoPError("DPoP proof iat outside acceptable clock skew")

        jti = payload.get("jti")
        if not jti:
            raise DPoPError("DPoP proof missing jti claim")
        if len(jti) > DPOP_JTI_MAX_LENGTH:
            raise DPoPError("DPoP proof jti too large")

        jti_hash = hashlib.sha256(jti.encode("utf-8")).hexdigest()
        cache_key = CACHE_KEY_DPOP_JTI % jti_hash
        # Use atomic add to prevent TOCTOU race.  Wrap in a savepoint so
        # that cache backends which raise IntegrityError on duplicate keys
        # do not abort the outer transaction.
        try:
            with transaction.atomic():
                added = cache.add(cache_key, True, timeout=DPOP_JTI_REPLAY_WINDOW)
        except DatabaseError:
            added = False
        if not added:
            raise DPoPError("DPoP proof jti replay detected")

        if expected_c_s256 is not None:
            proof_c_s256 = payload.get("c_s256")
            if proof_c_s256 is None:
                raise DPoPError("DPoP proof missing required c_s256 claim")
            if not compare_digest(proof_c_s256, expected_c_s256):
                raise DPoPError("DPoP proof c_s256 mismatch")

        if expected_jkt is not None:
            thumbprint = jwk_thumbprint(jwk)
            if not compare_digest(thumbprint, expected_jkt):
                raise DPoPError("DPoP proof JWK thumbprint mismatch")

        return jwk

    def _validate_jwk(self, jwk: dict) -> None:
        """Ensure the JWK is a public asymmetric key without private material"""
        kty = jwk.get("kty")
        if kty not in DPOP_SUPPORTED_KTYS:
            raise DPoPError(f"Unsupported JWK kty for DPoP: {kty}")

        if kty == "RSA":
            # n is base64url-encoded big-endian modulus
            n = jwk.get("n", "")
            # len(base64url(n)) * 6 bits ≈ key size; 342 chars ≈ 2048 bits
            if len(n) < 342:
                raise DPoPError("RSA key is too small for DPoP (minimum 2048 bits)")
        elif kty == "EC":
            crv = jwk.get("crv")
            if crv not in {"P-256", "P-384", "P-521"}:
                raise DPoPError(f"Unsupported EC curve for DPoP: {crv}")

        private_fields = {"d", "p", "q", "dp", "dq", "qi"}
        if any(field in jwk for field in private_fields):
            raise DPoPError("DPoP JWK must not contain private key material")

    def _htu_matches(self, proof_htu: str, expected_htu: str) -> bool:
        """Compare htu values ignoring query string and fragment"""
        parsed_proof = urlparse(proof_htu)
        parsed_expected = urlparse(expected_htu)
        return (
            parsed_proof.scheme == parsed_expected.scheme
            and parsed_proof.netloc == parsed_expected.netloc
            and parsed_proof.path == parsed_expected.path
        )
