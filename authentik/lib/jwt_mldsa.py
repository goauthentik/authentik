"""ML-DSA (FIPS 204) signature algorithms for PyJWT, per RFC 9964.

PyJWT ships no post-quantum algorithms. This module registers `ML-DSA-44`, `ML-DSA-65` and
`ML-DSA-87` with PyJWT's global JWS instance, backed by cryptography's ML-DSA keys, so every
existing `jwt.encode` / `jwt.decode` call site can sign and verify ML-DSA tokens unchanged.

JWK representation (RFC 9964): `kty` is `AKP`, `alg` names the parameter set, `pub` carries the
raw public key and `priv` the raw private key, both base64url encoded.

This module is imported during process setup (see authentik.root.setup) and must not import
Django."""

from json import loads
from typing import Any

from cryptography.exceptions import InternalError, InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric import mldsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from jwt import PyJWK, register_algorithm
from jwt.algorithms import Algorithm
from jwt.exceptions import InvalidKeyError
from jwt.utils import base64url_decode, base64url_encode

JWK_KTY_AKP = "AKP"

# Raised by cryptography when key material is malformed (ValueError) or when OpenSSL has no
# implementation for the algorithm in the current configuration, for example ML-DSA under a FIPS
# provider that predates it (InternalError / UnsupportedAlgorithm). All three mean the key is
# unusable here, so they surface as InvalidKeyError for the JWT call sites to handle.
KEY_LOAD_ERRORS = (ValueError, InternalError, UnsupportedAlgorithm)

MLDSAKey = (
    mldsa.MLDSA44PrivateKey
    | mldsa.MLDSA44PublicKey
    | mldsa.MLDSA65PrivateKey
    | mldsa.MLDSA65PublicKey
    | mldsa.MLDSA87PrivateKey
    | mldsa.MLDSA87PublicKey
)

# JOSE algorithm name -> (private key class, public key class)
MLDSA_ALGORITHMS: dict[str, tuple[type, type]] = {
    "ML-DSA-44": (mldsa.MLDSA44PrivateKey, mldsa.MLDSA44PublicKey),
    "ML-DSA-65": (mldsa.MLDSA65PrivateKey, mldsa.MLDSA65PublicKey),
    "ML-DSA-87": (mldsa.MLDSA87PrivateKey, mldsa.MLDSA87PublicKey),
}


class MLDSAAlgorithm(Algorithm):
    """PyJWT signature algorithm for one ML-DSA parameter set"""

    def __init__(self, name: str):
        self.name = name
        self.private_key_cls, self.public_key_cls = MLDSA_ALGORITHMS[name]
        self._crypto_key_types = (self.private_key_cls, self.public_key_cls)

    def prepare_key(self, key: Any) -> MLDSAKey:
        if isinstance(key, str | bytes):
            key_bytes = key.encode("utf-8") if isinstance(key, str) else key
            try:
                if b"-----BEGIN PUBLIC" in key_bytes:
                    key = load_pem_public_key(key_bytes)
                elif b"-----BEGIN PRIVATE" in key_bytes:
                    key = load_pem_private_key(key_bytes, password=None)
                else:
                    raise InvalidKeyError("Not a PEM public or private key")
            except KEY_LOAD_ERRORS as exc:
                raise InvalidKeyError(f"Unable to load {self.name} key: {exc}") from exc
        if not isinstance(key, self._crypto_key_types):
            raise InvalidKeyError(f"Expected a {self.name} key, got {type(key).__name__}")
        return key

    def sign(self, msg: bytes, key: Any) -> bytes:
        if not isinstance(key, self.private_key_cls):
            raise InvalidKeyError(f"A {self.name} private key is required to sign")
        return key.sign(msg)

    def verify(self, msg: bytes, key: Any, sig: bytes) -> bool:
        public_key = key.public_key() if isinstance(key, self.private_key_cls) else key
        try:
            public_key.verify(sig, msg)
            return True
        except InvalidSignature:
            return False

    @staticmethod
    def to_jwk(key_obj: Any, as_dict: bool = False) -> dict | str:
        name = algorithm_for_key(key_obj)
        private_key_cls, _ = MLDSA_ALGORITHMS[name]
        jwk: dict[str, str] = {"kty": JWK_KTY_AKP, "alg": name}
        if isinstance(key_obj, private_key_cls):
            jwk["priv"] = base64url_encode(key_obj.private_bytes_raw()).decode("ascii")
            key_obj = key_obj.public_key()
        jwk["pub"] = base64url_encode(key_obj.public_bytes_raw()).decode("ascii")
        if as_dict:
            return jwk
        from json import dumps

        return dumps(jwk)

    @staticmethod
    def from_jwk(jwk: str | dict) -> MLDSAKey:
        data = loads(jwk) if isinstance(jwk, str) else jwk
        if data.get("kty") != JWK_KTY_AKP:
            raise InvalidKeyError("Not an AKP key")
        name = data.get("alg")
        if name not in MLDSA_ALGORITHMS:
            raise InvalidKeyError(f"Unsupported AKP algorithm: {name}")
        private_key_cls, public_key_cls = MLDSA_ALGORITHMS[name]
        try:
            if "priv" in data:
                return private_key_cls.from_private_bytes(base64url_decode(data["priv"]))
            if "pub" in data:
                return public_key_cls.from_public_bytes(base64url_decode(data["pub"]))
        except KEY_LOAD_ERRORS as exc:
            raise InvalidKeyError(f"Invalid {name} key: {exc}") from exc
        raise InvalidKeyError("AKP key has neither pub nor priv")


def algorithm_for_key(key: Any) -> str:
    """Return the JOSE algorithm name for an ML-DSA key, or raise ValueError"""
    for name, classes in MLDSA_ALGORITHMS.items():
        if isinstance(key, classes):
            return name
    raise ValueError(f"Not an ML-DSA key: {type(key).__name__}")


def is_mldsa_key(key: Any) -> bool:
    """Whether the key is an ML-DSA private or public key"""
    return isinstance(key, MLDSAKey)


def key_from_jwk(jwk: dict) -> tuple[Any, str]:
    """Load a JWK into a cryptography key and return it with its JOSE algorithm.

    PyJWT's own JWK loader only knows the key types it ships with, so AKP keys are handled here
    and everything else is delegated to PyJWK."""
    if jwk.get("kty") == JWK_KTY_AKP:
        return MLDSAAlgorithm.from_jwk(jwk), jwk["alg"]
    parsed = PyJWK.from_dict(jwk)
    return parsed.key, parsed.algorithm_name


def register_mldsa_algorithms():
    """Register the ML-DSA algorithms with PyJWT's global JWS instance (idempotent)"""
    for name in MLDSA_ALGORITHMS:
        try:
            register_algorithm(name, MLDSAAlgorithm(name))
        except ValueError:
            # Already registered
            pass
