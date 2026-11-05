"""Asymmetric (``private_key_jwt``) client authentication primitives

This module parses the client credentials presented at an OAuth endpoint and verifies
JWT client assertions (RFC 7521 section 4.2, RFC 7523 sections 2.2 and 3, OpenID
Connect Core section 9 ``private_key_jwt``) against keys and a policy supplied by the
caller. It does not decide *which* clients may use ``private_key_jwt``, and it does not
fetch keys. Callers that support this method supply:

- a ``ClientKeySource``, the locally trusted public keys for one client. Fetching,
  caching and rotating remote key sets is the key source's concern, not this module's.
- a ``ClientAssertionPolicy``, the accepted audience, algorithms and time bounds.

Keys, algorithms, ``typ`` matching and the replay record are the shared JOSE primitives
of ``authentik.providers.oauth2.jose``.

Nothing in core enables this method for existing clients; it is only reachable through
callers that explicitly provide keys and a policy.

Client assertions are kept separate from the JWT *grant* ``assertion`` and from the
federated JWTs accepted by the ``client_credentials`` grant: a verified client assertion
authenticates the client and nothing else. It never grants scopes, identifies a user or
otherwise authorizes a request.

Validation is stricter than RFC 7523 requires in some places. Those are local policy
choices, marked "Local policy" below:

- ``iat`` and ``jti`` are required (both are optional in RFC 7523; OIDC requires ``jti``
  and single use).
- The audience must be a single value (a string or a one element array), matching the
  authorization server's issuer identifier exactly (draft-ietf-oauth-rfc7523bis: the
  token endpoint URL must not be used). Accepting the token endpoint URL as well, as
  older OpenID Connect clients send, is an explicit opt-in (``AssertionAudience``).
- Assertions older than ``max_age`` or with a lifetime over ``max_lifetime`` are rejected.
- Keys are only selected by ``kid``. Without a ``kid`` the key set must hold exactly one
  key (OIDC Core section 10.1 requires a ``kid`` when there are several).
- ``typ``, when present, must be ``JWT`` or ``client-authentication+jwt``.
- Any ``crit`` header and any key location or embedded key header (``jku``, ``x5u``,
  ``jwk``, ``x5c``) is rejected, rather than ignored.
"""

import math
import time
from base64 import b64decode
from binascii import Error as BinasciiError
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import unquote

from django.http import HttpRequest
from jwt import decode as jwt_decode
from jwt import decode_complete as jwt_decode_complete
from jwt import get_unverified_header
from jwt.exceptions import (
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidSignatureError,
    PyJWTError,
)
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import (
    CLIENT_ASSERTION,
    CLIENT_ASSERTION_TYPE,
    CLIENT_ASSERTION_TYPE_JWT,
)
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.jose import (
    ALGORITHMS,
    DEFAULT_ALGORITHMS,
    KEY_LOCATION_HEADERS,
    MAX_KID_LENGTH,
    TrustedKey,
    consume_jti,
    jwt_typ_matches,
    usable_algorithms,
)

if TYPE_CHECKING:
    from authentik.providers.oauth2.client import OAuthClientContext

LOGGER = get_logger()


class ClientAuthMethod(StrEnum):
    """Token endpoint authentication methods, as registered in the IANA "OAuth Token
    Endpoint Authentication Methods" registry"""

    NONE = "none"
    CLIENT_SECRET_BASIC = "client_secret_basic"  # nosec
    CLIENT_SECRET_POST = "client_secret_post"  # nosec
    PRIVATE_KEY_JWT = "private_key_jwt"


# Accepted `typ` header values (RFC 7515 section 4.1.9 comparison, see
# `jwt_typ_matches`). Explicitly typed JWTs for other purposes (at+jwt, dpop+jwt, ...)
# are rejected.
ACCEPTED_TYPES = ("JWT", "client-authentication+jwt")

# Bounds on attacker controlled sizes
MAX_ASSERTION_LENGTH = 8192
MAX_JTI_LENGTH = 256

# `consume_jti` namespace of client assertions
JTI_NAMESPACE = "client_assertion"


class ClientAuthenticationError(TokenError):
    """Client authentication failed.

    ``cause`` is a fixed, machine readable reason that is safe to log. It never contains
    any part of the presented credentials."""

    def __init__(self, cause: str, error: str = "invalid_client"):
        super().__init__(error)
        self.with_cause(cause)

    def __str__(self) -> str:
        return f"{self.error}: {self.cause}"


@dataclass(frozen=True, slots=True)
class PresentedClientCredentials:
    """Client credentials as presented in a request. Nothing here is authenticated.

    For ``private_key_jwt``, ``client_id`` is either the ``client_id`` parameter or, when
    that is absent, the assertion's unverified ``sub`` claim. It may only be used to look
    up the client whose keys will verify the assertion."""

    method: ClientAuthMethod
    client_id: str
    client_secret: str | None = field(default=None, repr=False)
    client_assertion: str | None = field(default=None, repr=False)


def _single_param(request: HttpRequest, name: str) -> str | None:
    values = request.POST.getlist(name)
    if len(values) > 1:
        # RFC 6749 section 3.2: parameters MUST NOT be included more than once
        raise ClientAuthenticationError("duplicate_parameter", "invalid_request")
    return values[0] if values else None


def _basic_credentials(request: HttpRequest) -> tuple[str, str] | None:
    header = request.META.get("HTTP_AUTHORIZATION", "")
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "basic":
        return None
    try:
        decoded = b64decode(value.strip(), validate=True).decode("utf-8")
    except BinasciiError, UnicodeDecodeError, ValueError:
        raise ClientAuthenticationError("malformed_basic_credentials") from None
    client_id, sep, client_secret = decoded.partition(":")
    if not sep or not client_id:
        raise ClientAuthenticationError("malformed_basic_credentials")
    # RFC 6749 section 2.3.1: Basic credentials are form encoded first. As in
    # `extract_client_auth`, only percent-decode so a raw `+` keeps its meaning.
    return unquote(client_id), unquote(client_secret)


def _unverified_subject(assertion: str) -> str:
    try:
        claims = jwt_decode_complete(
            assertion,
            options={"verify_signature": False},
        )["payload"]
    except PyJWTError, ValueError, TypeError:
        raise ClientAuthenticationError("malformed_assertion") from None
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise ClientAuthenticationError("malformed_assertion")
    return sub


def parse_client_credentials(request: HttpRequest) -> PresentedClientCredentials:
    """Parse the client credentials of a token endpoint style request, strictly.

    A request may use only one authentication method (RFC 6749 section 2.3). Mixing
    Basic credentials, a ``client_secret`` parameter and a client assertion fails, as do
    repeated parameters and credentials in the query string. An empty ``client_id`` or
    ``client_secret`` parameter counts as absent.

    This does not authenticate anything, and it is not used by the existing static client
    paths, which keep their current parsing."""
    for name in ("client_secret", CLIENT_ASSERTION, CLIENT_ASSERTION_TYPE):
        if name in request.GET:
            # RFC 6749 section 2.3.1: credentials MUST NOT be included in the request URI
            raise ClientAuthenticationError("credentials_in_query", "invalid_request")

    basic = _basic_credentials(request)
    post_client_id = _single_param(request, "client_id") or None
    post_secret = _single_param(request, "client_secret") or None
    assertion = _single_param(request, CLIENT_ASSERTION)
    assertion_type = _single_param(request, CLIENT_ASSERTION_TYPE)

    if assertion is not None or assertion_type is not None:
        if basic is not None or post_secret is not None:
            raise ClientAuthenticationError("multiple_auth_methods", "invalid_request")
        if assertion_type != CLIENT_ASSERTION_TYPE_JWT:
            raise ClientAuthenticationError("unsupported_assertion_type")
        if not assertion:
            raise ClientAuthenticationError("missing_assertion", "invalid_request")
        if len(assertion) > MAX_ASSERTION_LENGTH:
            raise ClientAuthenticationError("malformed_assertion")
        subject = _unverified_subject(assertion)
        if post_client_id is not None and post_client_id != subject:
            raise ClientAuthenticationError("client_id_mismatch")
        return PresentedClientCredentials(
            method=ClientAuthMethod.PRIVATE_KEY_JWT,
            client_id=post_client_id or subject,
            client_assertion=assertion,
        )
    if basic is not None:
        if post_secret is not None:
            raise ClientAuthenticationError("multiple_auth_methods", "invalid_request")
        if post_client_id is not None and post_client_id != basic[0]:
            raise ClientAuthenticationError("client_id_mismatch", "invalid_request")
        return PresentedClientCredentials(
            method=ClientAuthMethod.CLIENT_SECRET_BASIC,
            client_id=basic[0],
            client_secret=basic[1],
        )
    if post_client_id is None:
        raise ClientAuthenticationError("missing_client_id")
    if post_secret is not None:
        return PresentedClientCredentials(
            method=ClientAuthMethod.CLIENT_SECRET_POST,
            client_id=post_client_id,
            client_secret=post_secret,
        )
    return PresentedClientCredentials(method=ClientAuthMethod.NONE, client_id=post_client_id)


class ClientKeysUnavailable(Exception):
    """Raised by a key source that cannot currently provide trustworthy keys (for example
    a failed fetch with no fresh cached copy). Verification fails closed."""


class ClientKeySource(Protocol):
    """The locally trusted public keys of a single client.

    ``get_keys(refresh=True)`` is called at most once per verification, only when the
    assertion names a ``kid`` that the current keys do not contain. It is triggered by
    unauthenticated input, so implementations must bound how often it actually refetches
    and must never return keys that are stale under their cache rules."""

    def get_keys(self, *, refresh: bool = False) -> Sequence[TrustedKey]: ...


@dataclass(frozen=True, slots=True)
class StaticClientKeySource:
    """Key source for a fixed, locally configured set of keys"""

    keys: tuple[TrustedKey, ...]

    def get_keys(self, *, refresh: bool = False) -> Sequence[TrustedKey]:
        return self.keys


@dataclass(frozen=True, slots=True)
class AssertionAudience:
    """The audience values a client assertion may name, compared exactly.

    ``issuer`` is the authorization server's issuer identifier, the only audience
    draft-ietf-oauth-rfc7523bis allows. ``token_endpoint`` is an explicit, per provider
    opt-in for clients that still send the token endpoint URL (OpenID Connect Core section
    9 used to recommend it); rfc7523bis says it MUST NOT be used, as an assertion naming
    an endpoint URL can be replayed by a malicious server mimicking that URL.

    Callers pass canonical, configured values; never values derived from the request's
    Host header."""

    issuer: str
    token_endpoint: str | None = None

    def __post_init__(self):
        if not isinstance(self.issuer, str) or not self.issuer:
            raise ValueError("A non-empty issuer is required")
        if self.token_endpoint is not None and (
            not isinstance(self.token_endpoint, str) or not self.token_endpoint
        ):
            raise ValueError("The token endpoint must be a non-empty string")

    @property
    def accepted(self) -> frozenset[str]:
        """All accepted audience values"""
        if self.token_endpoint is None:
            return frozenset({self.issuer})
        return frozenset({self.issuer, self.token_endpoint})


@dataclass(frozen=True, slots=True)
class ClientAssertionPolicy:
    """How client assertions are validated for a client.

    ``algorithms`` defaults to ``jose.DEFAULT_ALGORITHMS``; a caller may name others from
    ``jose.ALGORITHMS`` explicitly. Algorithms the current OpenSSL configuration cannot
    verify (EdDSA and ML-DSA in FIPS mode) are never accepted, whatever the policy says.
    Key sources build keys for algorithms beyond the default with the same set
    (``jose.parse_jwks(jwks, policy.algorithms)``)."""

    audience: AssertionAudience
    algorithms: frozenset[str] = DEFAULT_ALGORITHMS
    # Local policy: maximum seconds between `iat` and now
    max_age: int = 300
    # Local policy: maximum seconds between `iat` and `exp`
    max_lifetime: int = 3600
    # Accepted clock skew in seconds, for `exp`, `nbf` and future `iat`
    leeway: int = 30

    def __post_init__(self):
        if not isinstance(self.audience, AssertionAudience):
            raise ValueError("An AssertionAudience is required")
        if not self.algorithms or not self.algorithms <= ALGORITHMS.keys():
            raise ValueError("Algorithms must be a non-empty set of asymmetric algorithms")
        if not 0 < self.max_age <= self.max_lifetime <= 86400:  # noqa: PLR2004
            raise ValueError("Require 0 < max_age <= max_lifetime <= 86400")
        if not 0 <= self.leeway <= 300:  # noqa: PLR2004
            raise ValueError("Leeway must be between 0 and 300 seconds")


@dataclass(frozen=True, slots=True)
class VerifiedClientAssertion:
    """A verified client assertion. Proves only that the client holds the private key."""

    client_id: str
    key_id: str | None
    key_thumbprint: str
    algorithm: str
    audience: str
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ClientAuthentication:
    """The outcome of a successful client authentication: which client, and how. Later
    work binds grants to ``method``; it confers no authorization of its own."""

    client: OAuthClientContext
    method: ClientAuthMethod
    assertion: VerifiedClientAssertion | None = None


def _numeric_date(claims: Mapping[str, Any], name: str, required: bool) -> float | None:
    value = claims.get(name)
    if value is None:
        if required:
            raise ClientAuthenticationError("missing_claim")
        return None
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ClientAuthenticationError("invalid_claim")
    return float(value)


class ClientAssertionVerifier:
    """Verify ``private_key_jwt`` client assertions for one client"""

    def __init__(self, keys: ClientKeySource, policy: ClientAssertionPolicy):
        self.keys = keys
        self.policy = policy
        self.algorithms = usable_algorithms(policy.algorithms)

    def verify(self, assertion: str, client_id: str) -> VerifiedClientAssertion:
        """Verify ``assertion`` as authenticating ``client_id``, and record its ``jti`` so
        it cannot be used again. Raises ``ClientAuthenticationError``."""
        try:
            return self._verify(assertion, client_id)
        except ClientAuthenticationError as exc:
            # Never log the assertion or its claims
            LOGGER.info("Client assertion rejected", client_id=client_id, cause=exc.cause)
            raise

    def _verify(self, assertion: str, client_id: str) -> VerifiedClientAssertion:
        if not isinstance(assertion, str) or len(assertion) > MAX_ASSERTION_LENGTH:
            raise ClientAuthenticationError("malformed_assertion")
        # JWE (five part) and unsecured JWTs are not accepted
        if assertion.count(".") != 2:  # noqa: PLR2004
            raise ClientAuthenticationError("malformed_assertion")
        header = self._check_header(assertion)
        alg: str = header["alg"]
        key = self._select_key(header.get("kid"), alg)
        claims = self._decode(assertion, key, alg)
        verified = self._check_claims(claims, client_id, key, alg)
        self._record_jti(claims, client_id, verified)
        return verified

    def _check_header(self, assertion: str) -> dict[str, Any]:
        try:
            header = get_unverified_header(assertion)
        except PyJWTError, ValueError, TypeError:
            raise ClientAuthenticationError("malformed_assertion") from None
        if KEY_LOCATION_HEADERS & header.keys():
            raise ClientAuthenticationError("untrusted_key_location")
        # PyJWT already rejects unknown critical parameters; no extension is supported here
        if "crit" in header:
            raise ClientAuthenticationError("unsupported_critical_header")
        typ = header.get("typ")
        if typ is not None and not jwt_typ_matches(typ, *ACCEPTED_TYPES):
            raise ClientAuthenticationError("invalid_type")
        alg = header.get("alg")
        if not isinstance(alg, str) or alg not in self.algorithms:
            raise ClientAuthenticationError("unsupported_algorithm")
        kid = header.get("kid")
        if kid is not None and (not isinstance(kid, str) or not kid or len(kid) > MAX_KID_LENGTH):
            raise ClientAuthenticationError("malformed_assertion")
        return header

    def _get_keys(self, refresh: bool) -> Sequence[TrustedKey]:
        try:
            return self.keys.get_keys(refresh=refresh)
        except ClientKeysUnavailable:
            raise ClientAuthenticationError("keys_unavailable") from None

    def _select_key(self, kid: str | None, alg: str) -> TrustedKey:
        keys = self._get_keys(refresh=False)
        if kid is None:
            # Local policy, per OIDC Core section 10.1: without a kid, only a key set
            # holding a single key is unambiguous. Never try keys in turn.
            if len(keys) != 1:
                raise ClientAuthenticationError("ambiguous_key")
            matches = list(keys)
        else:
            matches = [key for key in keys if key.kid == kid]
            if not matches:
                # The client may have rotated its keys; let the key source refresh once
                matches = [key for key in self._get_keys(refresh=True) if key.kid == kid]
            if not matches:
                raise ClientAuthenticationError("unknown_key")
            if len(matches) > 1:
                raise ClientAuthenticationError("ambiguous_key")
        key = matches[0]
        if not key.supports(alg):
            raise ClientAuthenticationError("key_algorithm_mismatch")
        return key

    def _decode(self, assertion: str, key: TrustedKey, alg: str) -> dict[str, Any]:
        try:
            return jwt_decode(
                assertion,
                key.key,
                # Exactly the algorithm already checked against the policy and the key
                algorithms=[alg],
                leeway=self.policy.leeway,
                options={
                    "require": ["iss", "sub", "aud", "exp", "iat", "jti"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    # Checked below, exactly and against configured values only
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
        except ExpiredSignatureError:
            raise ClientAuthenticationError("expired") from None
        except ImmatureSignatureError:
            raise ClientAuthenticationError("not_yet_valid") from None
        except InvalidSignatureError:
            raise ClientAuthenticationError("invalid_signature") from None
        except PyJWTError, ValueError, TypeError:
            raise ClientAuthenticationError("invalid_claims") from None

    def _check_claims(
        self, claims: Mapping[str, Any], client_id: str, key: TrustedKey, alg: str
    ) -> VerifiedClientAssertion:
        policy = self.policy
        # RFC 7523 section 3 and OIDC Core section 9: iss and sub are the client_id,
        # compared as simple strings
        if claims.get("iss") != client_id:
            raise ClientAuthenticationError("invalid_issuer")
        if claims.get("sub") != client_id:
            raise ClientAuthenticationError("invalid_subject")
        aud = claims.get("aud")
        if isinstance(aud, list) and len(aud) == 1:
            aud = aud[0]
        if not isinstance(aud, str) or aud not in policy.audience.accepted:
            raise ClientAuthenticationError("invalid_audience")
        jti = claims.get("jti")
        if not isinstance(jti, str) or not jti or len(jti) > MAX_JTI_LENGTH:
            raise ClientAuthenticationError("invalid_claim")

        now = time.time()
        iat = _numeric_date(claims, "iat", required=True)
        exp = _numeric_date(claims, "exp", required=True)
        nbf = _numeric_date(claims, "nbf", required=False)
        assert iat is not None and exp is not None  # nosec
        if exp <= now - policy.leeway:
            raise ClientAuthenticationError("expired")
        if iat > now + policy.leeway or (nbf is not None and nbf > now + policy.leeway):
            raise ClientAuthenticationError("not_yet_valid")
        if exp <= iat or exp - iat > policy.max_lifetime:
            raise ClientAuthenticationError("lifetime_exceeded")
        if now - iat > policy.max_age:
            raise ClientAuthenticationError("too_old")
        return VerifiedClientAssertion(
            client_id=client_id,
            key_id=key.kid,
            key_thumbprint=key.thumbprint,
            algorithm=alg,
            audience=aud,
            issued_at=datetime.fromtimestamp(iat, tz=UTC),
            expires_at=datetime.fromtimestamp(exp, tz=UTC),
        )

    def _record_jti(
        self, claims: Mapping[str, Any], client_id: str, verified: VerifiedClientAssertion
    ) -> None:
        """Atomically record the assertion's jti, failing if it was already used, or if
        it cannot be recorded.

        jti values are unique per issuer, so the record is scoped to the client (the
        issuer) and, through the cache key function, the tenant. It is shared by every
        provider that trusts this client, so an assertion accepted by one cannot be
        replayed at another. The record lives until the assertion would be rejected
        anyway for being expired or too old, so the table stays bounded by the policy's
        time window."""
        policy = self.policy
        accept_until = min(
            verified.expires_at.timestamp() + policy.leeway,
            verified.issued_at.timestamp() + policy.max_age,
        )
        if not consume_jti(JTI_NAMESPACE, client_id, claims["jti"], accept_until):
            raise ClientAuthenticationError("replayed")


def authenticate_private_key_jwt(
    credentials: PresentedClientCredentials,
    client: OAuthClientContext,
    keys: ClientKeySource,
    policy: ClientAssertionPolicy,
) -> ClientAuthentication:
    """Authenticate ``client`` with the presented ``private_key_jwt`` credentials.

    The caller has resolved ``client`` from ``credentials.client_id`` and decided that
    this client authenticates with ``private_key_jwt``; any other presented method fails,
    so a client required to use asymmetric authentication cannot fall back to a secret
    or to ``none``."""
    if credentials.method != ClientAuthMethod.PRIVATE_KEY_JWT or not credentials.client_assertion:
        LOGGER.info(
            "Client authentication method not allowed",
            client_id=client.client_id,
            method=credentials.method,
        )
        raise ClientAuthenticationError("auth_method_not_allowed")
    if credentials.client_id != client.client_id:
        raise ClientAuthenticationError("client_id_mismatch")
    verified = ClientAssertionVerifier(keys, policy).verify(
        credentials.client_assertion, client.client_id
    )
    return ClientAuthentication(
        client=client, method=ClientAuthMethod.PRIVATE_KEY_JWT, assertion=verified
    )
