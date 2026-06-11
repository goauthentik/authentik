"""DPoP (Demonstrating Proof-of-Possession) utils"""

import base64
import hashlib
import time
from hmac import compare_digest
from urllib.parse import urlparse

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from django.core.cache import cache
from django.db import DatabaseError, transaction
from jwt import PyJWK
from jwt import decode as jwt_decode
from jwt import decode_complete as jwt_decode_complete
from jwt.exceptions import InvalidTokenError, PyJWTError
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()

# Clock skew tolerance in seconds for `iat` validation
DPOP_IAT_CLOCK_SKEW = 60

# DPoP JWT type header value
DPOP_JWT_TYPE = "dpop+jwt"

# Supported asymmetric key types for DPoP
DPOP_SUPPORTED_KTYS = {"EC", "RSA"}

DPOP_SUPPORTED_EC_CURVES = {"P-256", "P-384", "P-521"}

# RSA key size limits for DPoP (bits)
DPOP_RSA_MIN_KEY_SIZE = 2048
DPOP_RSA_MAX_KEY_SIZE = 8192

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

# Required JWK members per RFC 7638, by key type. These are exactly the
# members the thumbprint is computed over, so a JWK rebuilt from only these
# has the same thumbprint and carries no additional user supplied extra
# claims (kid, alg, use, key_ops, x5c, x5u, jku, or unknown members).
JWK_REQUIRED_CLAIMS = {
    "EC": ("crv", "kty", "x", "y"),
    "RSA": ("e", "kty", "n"),
}

# JTI replay protection window in seconds
DPOP_JTI_REPLAY_WINDOW = int(CONFIG.get("providers.oauth2.dpop_jti_replay_window", 180))

# Maximum allowed JTI length
DPOP_JTI_MAX_LENGTH = 256

# Cache key template for tracked JTIs
CACHE_KEY_DPOP_JTI = "authentik_providers_oauth2_dpop_jti_%s"


def jwk_thumbprint(jwk: dict) -> str:
    """Compute the SHA-256 JWK Thumbprint per RFC 7638"""
    key = PyJWK.from_dict(jwk)
    return key.thumbprint()


def code_sha256(value: str) -> str:
    """Compute c_s256: BASE64URL(SHA256(ASCII(value)))"""
    digest = hashlib.sha256(value.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def canonical_public_jwk(jwk: dict) -> dict:
    """Return a JWK containing only the RFC 7638 required public members."""
    kty = jwk.get("kty")
    members = JWK_REQUIRED_CLAIMS.get(kty)
    if members is None:
        raise DPoPError(f"Cannot canonicalize JWK of type {kty}")
    missing = [m for m in members if m not in jwk]
    if missing:
        raise DPoPError(f"JWK missing required members: {missing}")
    return {m: jwk[m] for m in members}


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
        header = self._extract_header(dpop_proof)
        jwk = self._get_and_validate_jwk(header)
        jwk = canonical_public_jwk(jwk)
        alg = self._get_and_validate_alg(header)
        payload = self._verify_signature(dpop_proof, jwk, alg)
        jti = self._validate_payload_claims(payload, expected_htm, expected_htu)
        self._check_jti_replay(jti)
        self._validate_optional_claims(payload, expected_c_s256, expected_jkt, jwk)
        return jwk

    def _extract_header(self, dpop_proof: str) -> dict:
        """Extract and return the unverified JOSE header."""
        try:
            unverified = jwt_decode_complete(
                dpop_proof,
                options={"verify_signature": False, "verify_exp": False, "verify_iat": False},
            )
            header = unverified.get("header", {})
        except PyJWTError as exc:
            raise DPoPError("Invalid DPoP proof JWT") from exc

        if header.get("typ") != DPOP_JWT_TYPE:
            raise DPoPError(f"Invalid DPoP typ header: {header.get('typ')}")
        return header

    def _get_and_validate_jwk(self, header: dict) -> dict:
        """Extract jwk from header and validate it."""
        jwk = header.get("jwk")
        if not isinstance(jwk, dict):
            raise DPoPError("Missing jwk in DPoP header")
        self._validate_jwk(jwk)
        return jwk

    def _get_and_validate_alg(self, header: dict) -> str:
        """Extract and validate the alg header."""
        alg = header.get("alg")
        if not alg:
            raise DPoPError("Missing alg in DPoP header")
        if alg not in DPOP_SUPPORTED_ALGS:
            raise DPoPError(f"Unsupported DPoP algorithm: {alg}")
        return alg

    def _verify_signature(self, dpop_proof: str, jwk: dict, alg: str) -> dict:
        """Verify the DPoP proof signature and return the payload."""
        try:
            key = PyJWK.from_dict(jwk)
            return jwt_decode(dpop_proof, key.key, algorithms=[alg], options={"verify_iat": False})
        except (PyJWTError, InvalidTokenError) as exc:
            raise DPoPError("DPoP proof signature verification failed") from exc

    def _validate_payload_claims(self, payload: dict, expected_htm: str, expected_htu: str) -> str:
        """Validate htm, htu, iat, jti claims. Return the jti value."""
        if payload.get("htm") != expected_htm:
            raise DPoPError(f"DPoP htm mismatch: expected {expected_htm}, got {payload.get('htm')}")

        payload_htu = payload.get("htu")
        if not payload_htu:
            raise DPoPError("DPoP proof missing htu claim")
        if not self._htu_matches(payload_htu, expected_htu):
            raise DPoPError(f"DPoP htu mismatch: expected {expected_htu}, got {payload_htu}")

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

        return jti

    def _check_jti_replay(self, jti: str) -> None:
        """Check if the jti has been seen before (replay protection)."""
        jti_hash = hashlib.sha256(jti.encode("utf-8")).hexdigest()
        cache_key = CACHE_KEY_DPOP_JTI % jti_hash
        if not cache.add(cache_key, True, timeout=DPOP_JTI_REPLAY_WINDOW):
            raise DPoPError("DPoP proof jti replay detected")

    def _validate_optional_claims(
        self,
        payload: dict,
        expected_c_s256: str | None,
        expected_jkt: str | None,
        jwk: dict,
    ) -> None:
        """Validate optional c_s256 and jkt claims if expected."""
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

    def _validate_jwk(self, jwk: dict) -> None:
        """Ensure the JWK is a public asymmetric key without private material"""
        kty = jwk.get("kty")
        if kty not in DPOP_SUPPORTED_KTYS:
            raise DPoPError(f"Unsupported JWK kty for DPoP: {kty}")

        if kty == "RSA":
            key = PyJWK.from_dict(jwk)
            if isinstance(key.key, RSAPublicKey) and key.key.key_size < DPOP_RSA_MIN_KEY_SIZE:
                raise DPoPError("RSA key too small for DPoP (minimum 2048 bits)")
            if isinstance(key.key, RSAPublicKey) and key.key.key_size > DPOP_RSA_MAX_KEY_SIZE:
                raise DPoPError("RSA key too large for DPoP")
        elif kty == "EC":
            crv = jwk.get("crv")
            if crv not in DPOP_SUPPORTED_EC_CURVES:
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
