"""Signature algorithms offered to WebAuthn authenticators"""

from collections.abc import Callable
from functools import cache, partial

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.mldsa import (
    MLDSA44PrivateKey,
    MLDSA44PublicKey,
    MLDSA65PrivateKey,
    MLDSA65PublicKey,
    MLDSA87PrivateKey,
    MLDSA87PublicKey,
)
from structlog.stdlib import get_logger
from webauthn.helpers.cose import COSEAlgorithmIdentifier

LOGGER = get_logger()

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


def _probe(private_key_class, public_key_class) -> None:
    """Round-trip a freshly generated key through the operations authentication needs"""
    private_key = private_key_class.generate()
    public_key = public_key_class.from_public_bytes(private_key.public_key().public_bytes_raw())
    public_key.verify(private_key.sign(b"authentik"), b"authentik")


# Algorithms whose availability depends on the OpenSSL provider in use. ES256 and RS256 are
# implemented by every provider authentik runs on, so they are not probed.
_PROBES: dict[COSEAlgorithmIdentifier, Callable[[], None]] = {
    COSEAlgorithmIdentifier.EDDSA: partial(_probe, Ed25519PrivateKey, Ed25519PublicKey),
    COSEAlgorithmIdentifier.ML_DSA_44: partial(_probe, MLDSA44PrivateKey, MLDSA44PublicKey),
    COSEAlgorithmIdentifier.ML_DSA_65: partial(_probe, MLDSA65PrivateKey, MLDSA65PublicKey),
    COSEAlgorithmIdentifier.ML_DSA_87: partial(_probe, MLDSA87PrivateKey, MLDSA87PublicKey),
}


@cache
def supported_pub_key_algs() -> list[COSEAlgorithmIdentifier]:
    """Algorithms offered to authenticators, limited to those the current OpenSSL configuration
    can verify. A credential is created on the authenticator with the first algorithm it supports,
    so offering one that cannot be verified later locks the user out at their first login.

    The validated OpenSSL FIPS provider, for example, implements neither Ed25519 nor ML-DSA, and
    cryptography reports both as a misleading key-length ValueError. The result is cached per
    process, as the provider cannot change after startup."""
    algs = []
    for alg in PREFERRED_PUB_KEY_ALGS:
        probe = _PROBES.get(alg)
        if probe:
            try:
                probe()
            except Exception as exc:  # noqa: BLE001
                LOGGER.info(
                    "Signature algorithm is not available in the current OpenSSL "
                    "configuration, not offering it to authenticators",
                    alg=alg.name,
                    exc=exc,
                )
                continue
        algs.append(alg)
    return algs
