"""Signature algorithms offered to WebAuthn authenticators"""

from cryptography.hazmat.backends.openssl.backend import backend
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers.decode_credential_public_key import decode_credential_public_key

# TODO: Remove the ML-DSA entries once py_webauthn adds ML-DSA to its default supported algorithms.
# Offered in order of preference, so the post-quantum ML-DSA sets (FIPS 204) are only
# chosen by an authenticator that supports none of the classical algorithms.
PREFERRED_PUB_KEY_ALGS = [
    COSEAlgorithmIdentifier.EDDSA,
    COSEAlgorithmIdentifier.ECDSA_SHA_256,
    COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
    COSEAlgorithmIdentifier.ML_DSA_44,
    COSEAlgorithmIdentifier.ML_DSA_65,
    COSEAlgorithmIdentifier.ML_DSA_87,
]

# TODO: Remove when OpenSSL/FIPS is updated
# The validated OpenSSL FIPS provider implements neither Ed25519 nor ML-DSA, so only these can
# be verified while FIPS mode is enabled.
FIPS_PUB_KEY_ALGS = [
    COSEAlgorithmIdentifier.ECDSA_SHA_256,
    COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
]

KEY_TYPE_NAMES = {
    COSEAlgorithmIdentifier.EDDSA: "EdDSA (Ed25519)",
    COSEAlgorithmIdentifier.ECDSA_SHA_256: "ES256",
    COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256: "RS256",
    COSEAlgorithmIdentifier.ML_DSA_44: "ML-DSA-44",
    COSEAlgorithmIdentifier.ML_DSA_65: "ML-DSA-65",
    COSEAlgorithmIdentifier.ML_DSA_87: "ML-DSA-87",
}


def supported_pub_key_algs() -> list[COSEAlgorithmIdentifier]:
    """Algorithms offered to authenticators, limited to those the current OpenSSL configuration
    can verify. A credential is created on the authenticator with the first algorithm it supports,
    so offering one that cannot be verified later locks the user out at their first login."""
    if backend._fips_enabled:
        return FIPS_PUB_KEY_ALGS
    return PREFERRED_PUB_KEY_ALGS


def credential_key_type(cose_public_key: bytes) -> str:
    """Human-readable key type of a stored COSE credential public key, for logs and errors"""
    try:
        alg = int(decode_credential_public_key(cose_public_key).alg)
    except Exception:  # noqa: BLE001
        return "unknown"
    try:
        identifier = COSEAlgorithmIdentifier(alg)
    except ValueError:
        return f"COSE algorithm {alg}"
    return KEY_TYPE_NAMES.get(identifier, identifier.name)
