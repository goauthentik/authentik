"""JOSE primitives for JWTs that third parties sign and present to authentik

Shared by every place that verifies a JWT signed by someone other than authentik: client
assertions (``private_key_jwt``), client metadata key sets and JWT authorization grants.
Keeping one copy of these rules means a key or algorithm accepted in one place is never
silently refused in another.

- ``ALGORITHMS`` is the one table of asymmetric signature algorithms. ``DEFAULT_ALGORITHMS``
  is what callers accept unless they explicitly opt into more (``asymmetric_algorithms``),
  and every set is filtered by what the running OpenSSL configuration can verify
  (``usable_algorithms``), which in FIPS mode excludes EdDSA and ML-DSA.
- ``TrustedKey`` and ``parse_jwks`` validate public JWKs.
- ``jwt_typ_matches`` compares ``typ`` header values.
- ``consume_jti`` is the shared single-use (replay) record.

Symmetric algorithms and ``none`` are never accepted (RFC 8725 section 3.1): a third
party's public key must never be usable as an HMAC secret.
"""

import hashlib
import json
import math
import time
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from django.core.cache import cache
from django.db import DatabaseError, transaction
from jwcrypto.common import JWException
from jwcrypto.jwk import JWK
from jwt import PyJWK
from jwt.exceptions import PyJWTError
from structlog.stdlib import get_logger

from authentik.lib.jwt_mldsa import JWK_KTY_AKP, MLDSA_ALGORITHMS, key_from_jwk

LOGGER = get_logger()


@dataclass(frozen=True, slots=True)
class JWSAlgorithm:
    """The key an asymmetric JWS algorithm verifies with"""

    kty: str
    # Required curve for EC and OKP keys
    crv: str | None
    # Implemented by the validated OpenSSL FIPS provider
    fips: bool


# TODO: Remove the `fips=False` exclusions when OpenSSL/FIPS is updated: the validated
# OpenSSL FIPS provider implements neither Ed25519 nor ML-DSA.
ALGORITHMS: Mapping[str, JWSAlgorithm] = {
    "RS256": JWSAlgorithm("RSA", None, fips=True),
    "RS384": JWSAlgorithm("RSA", None, fips=True),
    "RS512": JWSAlgorithm("RSA", None, fips=True),
    "PS256": JWSAlgorithm("RSA", None, fips=True),
    "PS384": JWSAlgorithm("RSA", None, fips=True),
    "PS512": JWSAlgorithm("RSA", None, fips=True),
    "ES256": JWSAlgorithm("EC", "P-256", fips=True),
    "ES384": JWSAlgorithm("EC", "P-384", fips=True),
    "ES512": JWSAlgorithm("EC", "P-521", fips=True),
    "EdDSA": JWSAlgorithm("OKP", "Ed25519", fips=False),
    **{name: JWSAlgorithm(JWK_KTY_AKP, None, fips=False) for name in MLDSA_ALGORITHMS},
}

# Accepted unless a caller explicitly opts into more. All of them are FIPS approved, so
# a client that works with one deployment keeps working when FIPS mode is turned on.
DEFAULT_ALGORITHMS = frozenset(
    {"RS256", "RS384", "RS512", "PS256", "PS384", "PS512", "ES256", "ES384", "ES512"}
)

RSA_MIN_KEY_SIZE = 2048
RSA_MAX_KEY_SIZE = 8192
MAX_KID_LENGTH = 256

# RFC 7638 required members, by key type: exactly the members a trusted key keeps, so
# nothing else a key set publishes (x5c, x5u, unknown members, ...) is carried along
JWK_PUBLIC_MEMBERS: Mapping[str, tuple[str, ...]] = {
    "RSA": ("e", "kty", "n"),
    "EC": ("crv", "kty", "x", "y"),
    "OKP": ("crv", "kty", "x"),
    # RFC 9964 section 5: alg is REQUIRED on AKP keys and is part of the thumbprint
    JWK_KTY_AKP: ("alg", "kty", "pub"),
}

# JWK members that carry private key material, for any key type
JWK_PRIVATE_MEMBERS = frozenset({"d", "p", "q", "dp", "dq", "qi", "oth", "k", "priv"})

# JOSE header parameters that point to, or embed, a verification key. Keys only ever come
# from locally trusted configuration, so callers reject these rather than ignore them.
KEY_LOCATION_HEADERS = frozenset({"jku", "x5u", "jwk", "x5c"})

CACHE_KEY_JTI = "goauthentik.io/providers/oauth2/jti/%s/%s"
# Extra seconds a jti record outlives the time it was asked to last. Cache expiry has a
# one second granularity; this keeps a record from expiring early.
JTI_RECORD_MARGIN = 5


def fips_enabled() -> bool:
    """Whether OpenSSL runs with the FIPS provider. Unlike the admin API's
    ``fips_enabled``, this is not gated on a license: it describes what can be verified."""
    return bool(backend._fips_enabled)


def usable_algorithms(algorithms: Iterable[str]) -> frozenset[str]:
    """The algorithms of ``algorithms`` that are asymmetric and can be verified by the
    current OpenSSL configuration. Unknown and symmetric names are dropped."""
    fips = fips_enabled()
    return frozenset(
        alg for alg in algorithms if alg in ALGORITHMS and (ALGORITHMS[alg].fips or not fips)
    )


def asymmetric_algorithms(*extensions: str) -> frozenset[str]:
    """``DEFAULT_ALGORITHMS``, plus ``extensions`` (for example ``EdDSA`` and the ML-DSA
    sets for JWT authorization grants), limited to what can currently be verified.

    Extensions must be named in ``ALGORITHMS``; anything else is a programming error."""
    unknown = set(extensions) - ALGORITHMS.keys()
    if unknown:
        raise ValueError(f"Unknown asymmetric algorithms: {sorted(unknown)}")
    return usable_algorithms(DEFAULT_ALGORITHMS | set(extensions))


class InvalidKey(ValueError):
    """A JWK cannot be used to verify signatures"""


def _accepted_key_types(algorithms: frozenset[str]) -> dict[str, set[str | None]]:
    """Key type -> accepted curves (``None`` for key types without curves)"""
    accepted: dict[str, set[str | None]] = {}
    for alg in algorithms:
        spec = ALGORITHMS[alg]
        accepted.setdefault(spec.kty, set()).add(spec.crv)
    return accepted


@dataclass(frozen=True, slots=True, eq=False)
class TrustedKey:
    """A locally trusted public signing key of a third party, built only from a validated
    public JWK."""

    kid: str | None
    # Algorithm the key is restricted to, if its JWK declared one (always set for AKP)
    alg: str | None
    kty: str
    crv: str | None
    public_jwk: Mapping[str, str] = field(repr=False)
    # RFC 7638 SHA-256 thumbprint
    thumbprint: str
    # The key to verify with: a cryptography public key
    key: Any = field(repr=False)

    @staticmethod
    def from_jwk(
        jwk: Mapping[str, Any], algorithms: Iterable[str] = DEFAULT_ALGORITHMS
    ) -> TrustedKey:
        """Validate a public JWK and build a trusted key from it.

        Only keys that can verify one of ``algorithms`` (after ``usable_algorithms``) are
        accepted. Raises ``InvalidKey`` for private, symmetric, unsupported, undersized
        or non signing keys."""
        usable = usable_algorithms(algorithms)
        if not isinstance(jwk, Mapping):
            raise InvalidKey("JWK is not an object")
        if JWK_PRIVATE_MEMBERS & jwk.keys():
            raise InvalidKey("JWK contains private or symmetric key material")
        accepted = _accepted_key_types(usable)
        kty = jwk.get("kty")
        if not isinstance(kty, str) or kty not in accepted:
            raise InvalidKey(f"Unsupported key type {kty!r}")
        if "use" in jwk and jwk["use"] != "sig":
            raise InvalidKey("Key is not a signing key")
        key_ops = jwk.get("key_ops")
        if key_ops is not None and (not isinstance(key_ops, list) or "verify" not in key_ops):
            raise InvalidKey("Key is not a verification key")
        kid = jwk.get("kid")
        if kid is not None and (not isinstance(kid, str) or not kid or len(kid) > MAX_KID_LENGTH):
            raise InvalidKey("Invalid kid")
        crv = jwk.get("crv") if kty in ("EC", "OKP") else None
        if crv not in accepted[kty]:
            raise InvalidKey(f"Unsupported curve {crv!r}")
        alg = jwk.get("alg")
        if alg is not None or kty == JWK_KTY_AKP:
            if alg not in usable:
                raise InvalidKey(f"Unsupported key algorithm {alg!r}")
            spec = ALGORITHMS[alg]
            if spec.kty != kty or (spec.crv is not None and spec.crv != crv):
                raise InvalidKey("Key algorithm does not match key type")
        members = JWK_PUBLIC_MEMBERS[kty]
        if not all(isinstance(jwk.get(m), str) for m in members):
            raise InvalidKey("JWK is missing required members")
        public_jwk = {m: jwk[m] for m in members}
        try:
            if kty == JWK_KTY_AKP:
                key, _ = key_from_jwk(public_jwk)
            else:
                key = PyJWK.from_dict(public_jwk).key
            thumbprint = JWK(**public_jwk).thumbprint()
        except (JWException, PyJWTError, ValueError, TypeError) as exc:
            raise InvalidKey("Invalid key material") from exc
        if isinstance(key, RSAPublicKey):
            if not RSA_MIN_KEY_SIZE <= key.key_size <= RSA_MAX_KEY_SIZE:
                raise InvalidKey("RSA key size out of bounds")
        elif not isinstance(
            key,
            (EllipticCurvePublicKey, Ed25519PublicKey)
            + tuple(public for _, public in MLDSA_ALGORITHMS.values()),
        ):
            raise InvalidKey("Not a public key")
        return TrustedKey(
            kid=kid,
            alg=alg,
            kty=kty,
            crv=crv,
            public_jwk=public_jwk,
            thumbprint=thumbprint,
            key=key,
        )

    def supports(self, alg: str) -> bool:
        """Whether this key may verify a signature made with ``alg``. Callers still check
        ``alg`` against their own accepted (and usable) algorithms."""
        if self.alg is not None and self.alg != alg:
            return False
        spec = ALGORITHMS.get(alg)
        if spec is None:
            return False
        return self.kty == spec.kty and (spec.crv is None or self.crv == spec.crv)


def parse_jwks(
    jwks: Mapping[str, Any], algorithms: Iterable[str] = DEFAULT_ALGORITHMS
) -> tuple[TrustedKey, ...]:
    """Build trusted keys from a JWK Set document.

    Keys that cannot verify any of ``algorithms`` (encryption keys, unsupported key types,
    key types not usable in FIPS mode) are skipped, so a JWT naming one of them fails as
    an unknown key. Private or symmetric key material anywhere in the set rejects the
    whole set, as does a ``kid`` used by more than one key."""
    if not isinstance(jwks, Mapping) or not isinstance(jwks.get("keys"), list):
        raise InvalidKey("Not a JWK Set")
    algorithms = frozenset(algorithms)
    keys = []
    for jwk in jwks["keys"]:
        if isinstance(jwk, Mapping) and JWK_PRIVATE_MEMBERS & jwk.keys():
            raise InvalidKey("JWK Set contains private or symmetric key material")
        try:
            keys.append(TrustedKey.from_jwk(jwk, algorithms))
        except InvalidKey as exc:
            LOGGER.debug("Skipping unusable key", reason=str(exc))
    kids = [key.kid for key in keys if key.kid is not None]
    if len(kids) != len(set(kids)):
        raise InvalidKey("Duplicate kid in JWK Set")
    return tuple(keys)


def _media_type(value: str) -> str:
    # RFC 7515 section 4.1.9: compared case insensitively, and a value without a "/" is
    # treated as if "application/" were prepended
    value = value.lower()
    return value if "/" in value else f"application/{value}"


def jwt_typ_matches(typ: Any, *accepted: str) -> bool:
    """Whether a JWT ``typ`` header value names one of the ``accepted`` media types.

    Case insensitive, with or without the ``application/`` prefix, on either side. A
    missing (``None``) or non-string ``typ`` never matches; callers for which ``typ`` is
    optional check for its absence themselves."""
    if not isinstance(typ, str) or not typ:
        return False
    return _media_type(typ) in {_media_type(value) for value in accepted}


def consume_jti(namespace: str, issuer: str, jti: str, until: float) -> bool:
    """Record that ``issuer`` used ``jti``, atomically. Returns True the first time, and
    False if it was already recorded, so a JWT can be accepted only once.

    ``namespace`` separates JWT purposes (``client_assertion``, ``id_jag``, ...); ``jti``
    values are unique per issuer (RFC 7519 section 4.1.7), so the record is scoped to
    both. The cache key function adds the tenant. Only a hash is stored. ``until`` (a
    POSIX timestamp) is when the JWT would be rejected anyway, for example its ``exp``
    plus leeway; callers bound it, as the record lives that long.

    The record is an insert-if-absent in the shared PostgreSQL cache, so it holds across
    workers. It fails closed: a cache that cannot record the jti refuses it (``add``
    returns False for most database errors, and errors it raises are caught here). The
    savepoint keeps a failed insert from breaking an outer transaction."""
    timeout = max(1, math.ceil(until - time.time())) + JTI_RECORD_MARGIN
    digest = hashlib.sha256(
        json.dumps([namespace, issuer, jti], separators=(",", ":")).encode()
    ).hexdigest()
    try:
        with transaction.atomic():
            return bool(cache.add(CACHE_KEY_JTI % (namespace, digest), True, timeout=timeout))
    except DatabaseError as exc:
        LOGGER.warning("jti replay cache unavailable", namespace=namespace, exc=exc)
        return False
