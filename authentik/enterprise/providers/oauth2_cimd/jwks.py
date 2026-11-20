"""Validation of client JSON Web Key Sets: public, asymmetric signing keys only"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from jwcrypto.jwk import JWK
from jwt import PyJWK
from jwt.exceptions import PyJWTError

from authentik.enterprise.providers.oauth2_cimd.constants import (
    EC_ALG_CURVES,
    MAX_JWKS_KEYS,
    MAX_SHORT_STRING_LENGTH,
    OKP_CURVES,
    RSA_MAX_KEY_SIZE,
    RSA_MIN_KEY_SIZE,
    SIGNING_ALGS_BY_KTY,
)
from authentik.enterprise.providers.oauth2_cimd.errors import InvalidClientKeys

# Private key members (RFC 7518 section 6) and the symmetric key value
PRIVATE_MEMBERS = frozenset(("d", "p", "q", "dp", "dq", "qi", "oth", "k"))
# Public members kept per key type; everything else (x5c, x5u, jku, ...) is dropped
PUBLIC_MEMBERS = {
    "RSA": ("n", "e"),
    "EC": ("crv", "x", "y"),
    "OKP": ("crv", "x"),
}
_STRING_MEMBERS = ("kty", "kid", "alg", "use", "crv", "n", "e", "x", "y")


@dataclass(frozen=True)
class ClientKey:
    """A validated public signing key"""

    kid: str | None
    kty: str
    alg: str | None
    # Public JWK members only (kty, kid, alg and the key-type parameters)
    jwk: Mapping[str, str]
    # RFC 7638 SHA-256 thumbprint
    thumbprint: str
    public_key: Any = field(compare=False, repr=False)

    @property
    def algorithms(self) -> frozenset[str]:
        """Algorithms this key may verify"""
        if self.alg:
            return frozenset((self.alg,))
        if self.kty == "EC":
            return frozenset(alg for alg, crv in EC_ALG_CURVES.items() if crv == self.jwk["crv"])
        return SIGNING_ALGS_BY_KTY[self.kty]


@dataclass(frozen=True)
class ClientKeySet:
    """Validated signing keys of a client"""

    keys: tuple[ClientKey, ...]

    def __bool__(self) -> bool:
        return bool(self.keys)

    def find(self, kid: str | None) -> ClientKey | None:
        """Key with ID `kid`; without a `kid`, the only key if there is exactly one"""
        if kid is None:
            return self.keys[0] if len(self.keys) == 1 else None
        for key in self.keys:
            if key.kid == kid:
                return key
        return None

    @property
    def kids(self) -> frozenset[str]:
        """All key IDs"""
        return frozenset(key.kid for key in self.keys if key.kid is not None)


def _is_signing_key(jwk: dict[str, Any]) -> bool:
    use = jwk.get("use")
    if use is not None and use != "sig":
        return False
    key_ops = jwk.get("key_ops")
    if key_ops is not None:
        if not isinstance(key_ops, list) or not all(isinstance(op, str) for op in key_ops):
            raise InvalidClientKeys("malformed_key", "key_ops must be a list of strings")
        return "verify" in key_ops
    return True


def _check_alg(kty: str, alg: str | None, crv: str | None) -> None:
    if alg is None:
        return
    if alg not in SIGNING_ALGS_BY_KTY[kty]:
        raise InvalidClientKeys(
            "unsupported_alg", "Key algorithm is not an allowed signing algorithm"
        )
    if kty == "EC" and EC_ALG_CURVES[alg] != crv:
        raise InvalidClientKeys("malformed_key", "Key algorithm does not match curve")


def _validate_key(jwk: Any) -> ClientKey | None:
    """Validate one key. Returns None for keys that are not usable for signing,
    raises InvalidClientKeys for malformed, private or symmetric keys."""
    if not isinstance(jwk, dict):
        raise InvalidClientKeys("malformed_key", "Key must be an object")
    if PRIVATE_MEMBERS & jwk.keys():
        raise InvalidClientKeys("private_key", "Key contains private key material")
    for name in _STRING_MEMBERS:
        value = jwk.get(name)
        if value is not None and not isinstance(value, str):
            raise InvalidClientKeys("malformed_key", f"Key member {name} must be a string")
    kty = jwk.get("kty")
    if kty is None:
        raise InvalidClientKeys("malformed_key", "Key has no kty")
    if kty == "oct":
        raise InvalidClientKeys("symmetric_key", "Symmetric keys are not allowed")
    if kty not in PUBLIC_MEMBERS:
        # Unknown key types are ignored (RFC 7517 section 5)
        return None
    if not _is_signing_key(jwk):
        return None
    kid = jwk.get("kid")
    if kid is not None and not 0 < len(kid) <= MAX_SHORT_STRING_LENGTH:
        raise InvalidClientKeys("malformed_key", "Invalid kid")
    alg = jwk.get("alg")
    crv = jwk.get("crv")
    _check_alg(kty, alg, crv)
    if kty == "EC" and crv not in EC_ALG_CURVES.values():
        raise InvalidClientKeys("unsupported_curve", "Unsupported EC curve")
    if kty == "OKP" and crv not in OKP_CURVES:
        raise InvalidClientKeys("unsupported_curve", "Unsupported OKP curve")
    missing = [name for name in PUBLIC_MEMBERS[kty] if name not in jwk]
    if missing:
        raise InvalidClientKeys("malformed_key", "Key is missing required members")
    public: dict[str, str] = {"kty": kty} | {name: jwk[name] for name in PUBLIC_MEMBERS[kty]}
    try:
        parsed = PyJWK.from_dict(public, algorithm=alg)
        thumbprint = JWK(**public).thumbprint()
    except (PyJWTError, ValueError, TypeError, KeyError) as exc:
        raise InvalidClientKeys("malformed_key", "Key could not be parsed") from exc
    if isinstance(parsed.key, RSAPublicKey) and not (
        RSA_MIN_KEY_SIZE <= parsed.key.key_size <= RSA_MAX_KEY_SIZE
    ):
        raise InvalidClientKeys("weak_key", "RSA key size is out of bounds")
    if kid is not None:
        public["kid"] = kid
    if alg is not None:
        public["alg"] = alg
    return ClientKey(
        kid=kid,
        kty=kty,
        alg=alg,
        jwk=MappingProxyType(public),
        thumbprint=thumbprint,
        public_key=parsed.key,
    )


def validate_jwks(jwks: Any) -> ClientKeySet:
    """Validate a JWK Set.

    The whole set is rejected if any key carries private or symmetric key
    material, is malformed, or if key IDs are duplicated. Keys of unknown types
    and encryption keys are skipped. The result may be empty."""
    if not isinstance(jwks, dict):
        raise InvalidClientKeys("malformed_jwks", "JWKS must be an object")
    keys = jwks.get("keys")
    if not isinstance(keys, list):
        raise InvalidClientKeys("malformed_jwks", "JWKS must contain a keys array")
    if len(keys) > MAX_JWKS_KEYS:
        raise InvalidClientKeys("too_many_keys", "JWKS contains too many keys")
    validated = tuple(key for key in (_validate_key(raw) for raw in keys) if key is not None)
    kids = [key.kid for key in validated if key.kid is not None]
    if len(kids) != len(set(kids)):
        raise InvalidClientKeys("duplicate_kid", "JWKS contains duplicate key IDs")
    return ClientKeySet(keys=validated)
