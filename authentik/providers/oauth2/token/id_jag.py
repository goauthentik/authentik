"""Redeem an ID-JAG (Identity Assertion JWT Authorization Grant) as a Resource Authorization
Server: RFC 7523 jwt-bearer, profiled by draft-ietf-oauth-identity-assertion-authz-grant-06
§4.4. The issuing side (authentik as IdP Authorization Server) lives in token_exchange.py.

Trust is configured with the provider's existing `jwt_federation_sources`: an OAuth source
with an OIDC well-known URL is a trusted IdP Authorization Server. Its issuer identifier is the
one that well-known URL is derived from (draft-06 §7.1, RFC 8414 §3.1, OIDC Discovery §4), and
its signing keys are the source's cached JWKS. The ID-JAG `sub` resolves to the user connected
to that source with the same identifier.
"""

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse

from django.core.cache import cache
from django.db import DatabaseError, transaction
from django.http import HttpRequest
from django.utils import timezone
from jwt import PyJWT, PyJWTError
from requests import RequestException

from authentik.core.models import Application, User
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION
from authentik.lib.jwt_mldsa import MLDSA_ALGORITHMS, key_from_jwk
from authentik.lib.utils.http import get_http_session
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import GRANT_RESOURCE_MAX_LENGTH, join_resources
from authentik.providers.oauth2.resources import (
    ResourceIndicatorError,
    allowed_resources,
    parse_resource_indicators,
)
from authentik.providers.oauth2.token.base import TokenRequest
from authentik.providers.oauth2.utils import is_all_vschar, is_id_jag_typ
from authentik.sources.oauth.jwks import cache_max_age, refresh_jwks
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

# draft-06 §3.1 REQUIRED claims
ID_JAG_REQUIRED_CLAIMS = ["iss", "sub", "aud", "client_id", "jti", "exp", "iat"]
# RFC 8725 §3.1: only asymmetric algorithms, so a trusted issuer's public key can't be used
# as an HMAC secret, and never `none`.
ID_JAG_ALGORITHMS = frozenset(
    {
        "RS256",
        "RS384",
        "RS512",
        "PS256",
        "PS384",
        "PS512",
        "ES256",
        "ES384",
        "ES512",
        "EdDSA",
        *MLDSA_ALGORITHMS,
    }
)
# Clock skew tolerated on exp, nbf, iat and auth_time, and added to how long a jti is
# remembered
ID_JAG_LEEWAY_SECONDS = 30
# Longest remaining lifetime accepted, so a jti is never remembered for longer. ID-JAGs are
# short-lived (draft-06 §3.1 recommends minutes); authentik issues them for 5 minutes.
ID_JAG_MAX_LIFETIME_SECONDS = 60 * 60
CACHE_KEY_ID_JAG_JTI = "goauthentik.io/providers/oauth2/id_jag/jti/%s"
# Set once a source's discovery document was confirmed to name the ID-JAG issuer, and its
# keys were fetched from the document's jwks_uri
CACHE_KEY_ID_JAG_ISSUER = "goauthentik.io/providers/oauth2/id_jag/issuer/%s"
# Set while a source's discovery document and keys may not be fetched again
CACHE_KEY_ID_JAG_FETCH = "goauthentik.io/providers/oauth2/id_jag/fetch/%s"
# How long a confirmed issuer and its keys are used before they're fetched again: the
# responses' Cache-Control max-age, else JWKS_CACHE_SECONDS, within these bounds
ID_JAG_ISSUER_MIN_CACHE_SECONDS = 60
ID_JAG_ISSUER_MAX_CACHE_SECONDS = 24 * 60 * 60
# Minimum time between fetches for one source, so assertions naming unknown keys can't make
# authentik fetch an issuer's keys on every request
ID_JAG_FETCH_INTERVAL_SECONDS = 30


def issuer_metadata_urls(issuer: str) -> set[str]:
    """Metadata URLs derived from an issuer identifier: RFC 8414 §3.1 path insertion, and the
    OpenID Connect Discovery §4 (and RFC 8414 §5 compatibility) suffix form."""
    parsed = urlparse(issuer)
    if not parsed.scheme or not parsed.netloc or parsed.query or parsed.fragment:
        return set()
    origin = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path.rstrip("/")
    base = issuer.rstrip("/")
    urls = {
        f"{origin}/.well-known/oauth-authorization-server{path}",
        f"{origin}/.well-known/openid-configuration{path}",
        f"{base}/.well-known/openid-configuration",
        f"{base}/.well-known/oauth-authorization-server",
    }
    # Issuers ending in "/" are also commonly served with it kept, as authentik does
    if path and parsed.path.endswith("/"):
        urls.add(f"{origin}/.well-known/oauth-authorization-server{path}/")
    return urls


class IdJagTokenRequest(TokenRequest):
    """RFC 7523 jwt-bearer grant, accepting only ID-JAGs (draft-06 §4.4.1)"""

    # The user the ID-JAG's subject resolves to
    user: User | None = None
    source: OAuthSource | None = None
    id_jag: dict[str, Any] | None = None
    # When the user authenticated at the issuer, if the ID-JAG says
    auth_time: datetime | None = None

    def parse(self, request: HttpRequest) -> None:
        super().parse(request)
        self.authenticate_client()
        assertion = request.POST.get("assertion", "")
        if not assertion:
            raise TokenError("invalid_request").with_cause("missing_assertion")
        self.id_jag = self.validate_id_jag(assertion, request)
        self.resolve_id_jag_resource(request)
        self.resolve_id_jag_scopes()

        app = Application.objects.filter(provider=self.provider).first()
        if not app or not app.provider:
            raise TokenError("invalid_grant").with_cause("provider_without_application")
        self.user = self.resolve_id_jag_user()
        # draft-06 §4.4.3: a valid ID-JAG whose user isn't authorized is `access_denied`
        try:
            self.check_policy_access(app, request, oauth_jwt=self.id_jag)
        except TokenError:
            raise TokenError("access_denied").with_cause("policy_denied") from None

        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "jwt",
                PLAN_CONTEXT_METHOD_ARGS: {"jwt": self.id_jag, "source": self.source},
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=self.user)

    def authenticate_client(self):
        """draft-06 §4.4: without a sender-constrained ID-JAG (not supported yet), the client
        MUST authenticate, so public clients can't redeem ID-JAGs."""
        if not self.client.is_confidential:
            raise TokenError("invalid_client").with_cause("public_client")
        if not is_all_vschar(self.client_secret) or not self.client.check_client_secret(
            self.client_secret
        ):
            raise TokenError("invalid_client").with_cause("invalid_secret")

    def trusted_source(self, issuer: str) -> OAuthSource | None:
        """The enabled federation source whose well-known URL is derived from `issuer`.
        Several could resolve users differently, so the issuer is then ambiguous and not
        trusted."""
        candidates = issuer_metadata_urls(issuer)
        if not candidates:
            return None
        sources = list(
            self.provider.jwt_federation_sources.filter(
                enabled=True, oidc_well_known_url__in=candidates
            )[:2]
        )
        if len(sources) > 1:
            self.logger.warning("Several federation sources trust the ID-JAG issuer", iss=issuer)
            raise TokenError("invalid_grant").with_cause("issuer_ambiguous")
        return sources[0] if sources else None

    def validate_id_jag(self, assertion: str, request: HttpRequest) -> dict[str, Any]:
        """RFC 7521 §5.2 and draft-06 §4.4.1. Every failure is `invalid_grant`."""
        try:
            unverified = PyJWT().decode_complete(assertion, options={"verify_signature": False})
        except PyJWTError, ValueError, TypeError, AttributeError:
            raise TokenError("invalid_grant").with_cause("malformed_assertion") from None
        header = unverified["header"]
        claims = unverified["payload"]
        if not is_id_jag_typ(header.get("typ")):
            raise TokenError("invalid_grant").with_cause("invalid_typ")
        alg = header.get("alg")
        if alg not in ID_JAG_ALGORITHMS:
            raise TokenError("invalid_grant").with_cause("invalid_alg")
        issuer = claims.get("iss")
        if not isinstance(issuer, str):
            raise TokenError("invalid_grant").with_cause("missing_iss")
        source = self.trusted_source(issuer)
        if not source:
            self.logger.info("ID-JAG from untrusted issuer")
            raise TokenError("invalid_grant").with_cause("untrusted_issuer")

        keys = self.issuer_keys(source, issuer, header.get("kid"))
        token = self.verify_signature(assertion, source, keys, header)
        # Signature, exp, iat and the required claims are verified; now the profile.
        own_issuer = self.provider.get_issuer(request)
        aud = token["aud"]
        if isinstance(aud, list):
            if len(aud) != 1:
                raise TokenError("invalid_grant").with_cause("invalid_aud")
            aud = aud[0]
        if not own_issuer or aud != own_issuer:
            raise TokenError("invalid_grant").with_cause("invalid_aud")
        # The client's identifier at this authorization server, which is the authenticated one
        if token["client_id"] != self.client.client_id:
            raise TokenError("invalid_grant").with_cause("client_id_mismatch")
        # Proof of possession (draft-06 §9.11) isn't implemented, so a sender-constrained
        # ID-JAG can't be honoured; accepting it as a bearer grant would drop the binding.
        if "cnf" in token:
            raise TokenError("invalid_grant").with_cause("cnf_unsupported")
        # `aud_tenant` (draft-06 §6) only selects a tenant of the Resource Authorization
        # Server. A provider is a single tenant, already selected by the token endpoint and
        # bound to its trusted issuers, so the claim is ignored rather than refused: clients
        # (Claude, for one) let administrators set it without the server asking for it.
        if not isinstance(token["sub"], str) or not token["sub"]:
            raise TokenError("invalid_grant").with_cause("invalid_sub")
        self.auth_time = self.parse_auth_time(token)
        self.check_jti_replay(token)
        self.source = source
        return token

    def issuer_keys(self, source: OAuthSource, issuer: str, kid: Any) -> list[dict[str, Any]]:
        """Signing keys of the trusted issuer. The source's discovery document must name
        `issuer` as its issuer, and the keys are those at the document's jwks_uri; keys
        carried in the assertion are never used. Both are confirmed when first used and again
        once the responses' max-age (by default an hour) has passed, and an assertion naming
        a `kid` the cached keys don't have fetches them again, so a rotated key is picked up
        immediately. Fetches for one source are at most every ID_JAG_FETCH_INTERVAL_SECONDS.

        Fails closed when the cache is unavailable: authentik's cache returns the default
        from `get` and False from `add` on a database error, and an exception from `add` is
        treated the same, so the issuer is not confirmed and nothing is fetched."""
        cache_id = sha256(
            f"{source.pk}\x00{source.oidc_well_known_url}\x00{issuer}".encode()
        ).hexdigest()
        keys = self.cached_keys(source)
        confirmed = cache.get(CACHE_KEY_ID_JAG_ISSUER % cache_id)
        if confirmed and (not kid or any(jwk.get("kid") == kid for jwk in keys)):
            return keys
        # In a savepoint, as a failed cache write must not break the request's transaction
        try:
            with transaction.atomic():
                may_fetch = cache.add(
                    CACHE_KEY_ID_JAG_FETCH % source.pk,
                    True,
                    timeout=ID_JAG_FETCH_INTERVAL_SECONDS,
                )
        except DatabaseError as exc:
            self.logger.warning("ID-JAG cache unavailable", exc=exc)
            may_fetch = False
        if not may_fetch:
            if confirmed:
                return keys
            self.logger.info("ID-JAG issuer not confirmed yet", source=source.slug)
            raise TokenError("invalid_grant").with_cause("issuer_unconfirmed")
        keys, max_age = self.fetch_issuer_keys(source, issuer)
        timeout = min(
            max(max_age, ID_JAG_ISSUER_MIN_CACHE_SECONDS), ID_JAG_ISSUER_MAX_CACHE_SECONDS
        )
        cache.set(CACHE_KEY_ID_JAG_ISSUER % cache_id, True, timeout=timeout)
        return keys

    @staticmethod
    def cached_keys(source: OAuthSource) -> list[dict[str, Any]]:
        keys = source.oidc_jwks.get("keys") if isinstance(source.oidc_jwks, dict) else None
        return [jwk for jwk in keys if isinstance(jwk, dict)] if isinstance(keys, list) else []

    def fetch_issuer_keys(
        self, source: OAuthSource, issuer: str
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch the source's discovery document, confirm that its `issuer` is the ID-JAG's,
        and fetch the keys at its jwks_uri. Only `issuer` and `jwks_uri` are required, as
        issuers that only sign assertions publish nothing else. The keys are stored on the
        source, like its scheduled refresh does. Returns them, and the shorter of the two
        responses' max-age."""
        try:
            response = get_http_session().get(source.oidc_well_known_url)
            response.raise_for_status()
            config = response.json()
        except (RequestException, ValueError) as exc:
            self.logger.warning(
                "Failed to fetch ID-JAG issuer metadata", source=source.slug, exc=exc
            )
            raise TokenError("invalid_grant").with_cause("issuer_metadata_unavailable") from None
        if not isinstance(config, dict) or config.get("issuer") != issuer:
            self.logger.warning(
                "ID-JAG issuer metadata names another issuer",
                source=source.slug,
                iss=issuer,
                metadata_issuer=config.get("issuer") if isinstance(config, dict) else None,
            )
            raise TokenError("invalid_grant").with_cause("issuer_mismatch")
        jwks_uri = config.get("jwks_uri")
        if not isinstance(jwks_uri, str) or not jwks_uri:
            raise TokenError("invalid_grant").with_cause("issuer_jwks_unavailable")
        metadata_max_age = cache_max_age(response)
        try:
            jwks_max_age = refresh_jwks(source, jwks_uri)
        except (RequestException, ValueError) as exc:
            self.logger.warning("Failed to fetch ID-JAG issuer keys", source=source.slug, exc=exc)
            raise TokenError("invalid_grant").with_cause("issuer_jwks_unavailable") from None
        return self.cached_keys(source), min(metadata_max_age, jwks_max_age)

    def verify_signature(
        self,
        assertion: str,
        source: OAuthSource,
        keys: list[dict[str, Any]],
        header: dict[str, Any],
    ) -> dict[str, Any]:
        kid = header.get("kid")
        for jwk in keys:
            if kid and jwk.get("kid") != kid:
                continue
            if jwk.get("use", "sig") != "sig":
                continue
            try:
                key, key_alg = key_from_jwk(jwk)
            except PyJWTError, ValueError, TypeError, KeyError:
                continue
            # A key pinned to an algorithm only verifies that algorithm
            if jwk.get("alg") and jwk["alg"] != header["alg"]:
                continue
            if key_alg not in ID_JAG_ALGORITHMS:
                continue
            try:
                return PyJWT().decode(
                    assertion,
                    key,
                    algorithms=[header["alg"]],
                    leeway=ID_JAG_LEEWAY_SECONDS,
                    options={
                        "require": ID_JAG_REQUIRED_CLAIMS,
                        # Checked against the issuer identifier afterwards, since the
                        # array form must have exactly one element
                        "verify_aud": False,
                        "verify_iat": True,
                    },
                )
            except PyJWTError as exc:
                self.logger.info("ID-JAG failed verification", source=source.slug, exc=exc)
                # Expiry and missing claims fail for every key; a wrong key may not
                continue
        raise TokenError("invalid_grant").with_cause("invalid_signature")

    @staticmethod
    def parse_auth_time(token: dict[str, Any]) -> datetime | None:
        """The optional `auth_time` claim (draft-06 §3.1, OIDC Core §2), which the issued
        access token keeps"""
        auth_time = token.get("auth_time")
        if auth_time is None:
            return None
        if isinstance(auth_time, bool) or not isinstance(auth_time, int | float):
            raise TokenError("invalid_grant").with_cause("invalid_auth_time")
        if auth_time > timezone.now().timestamp() + ID_JAG_LEEWAY_SECONDS:
            raise TokenError("invalid_grant").with_cause("invalid_auth_time")
        try:
            return datetime.fromtimestamp(auth_time, tz=UTC)
        except OverflowError, OSError, ValueError:
            raise TokenError("invalid_grant").with_cause("invalid_auth_time") from None

    def check_jti_replay(self, token: dict[str, Any]):
        """Accept each ID-JAG once (RFC 7523 §3, draft-06 §4.4.4), until it expires. Its
        lifetime is capped, and so is how long its jti is remembered.

        Fails closed when the cache is unavailable: authentik's cache returns False from
        `add` on a database error, which refuses the ID-JAG as replayed, and an exception
        from `add` is treated the same."""
        remaining = int(token["exp"]) - int(timezone.now().timestamp())
        if remaining > ID_JAG_MAX_LIFETIME_SECONDS:
            raise TokenError("invalid_grant").with_cause("lifetime_too_long")
        timeout = max(remaining, 0) + ID_JAG_LEEWAY_SECONDS
        key = sha256(f"{token['iss']}\x00{token['jti']}".encode()).hexdigest()
        try:
            with transaction.atomic():
                added = cache.add(CACHE_KEY_ID_JAG_JTI % key, True, timeout=timeout)
        except DatabaseError as exc:
            self.logger.warning("ID-JAG cache unavailable", exc=exc)
            added = False
        if not added:
            raise TokenError("invalid_grant").with_cause("jti_replayed")

    def resolve_id_jag_resource(self, request: HttpRequest):
        """draft-06 §4.4.1: every `resource` the ID-JAG names must be governed by this
        authorization server, which are the resources allowed for the client (RFC 8707). The
        access token is restricted to them, like a grant restricted to resources: a `resource`
        parameter may narrow it further, never widen it."""
        claimed = self.id_jag.get("resource")
        granted: tuple[str, ...] = ()
        if claimed is not None:
            values = [claimed] if isinstance(claimed, str) else claimed
            if (
                not isinstance(values, list)
                or not values
                or not all(isinstance(value, str) for value in values)
            ):
                raise TokenError("invalid_grant").with_cause("invalid_resource_claim")
            try:
                granted = parse_resource_indicators(values)
            except ResourceIndicatorError:
                raise TokenError("invalid_grant").with_cause("invalid_resource_claim") from None
            if len(join_resources(granted) or "") > GRANT_RESOURCE_MAX_LENGTH:
                raise TokenError("invalid_grant").with_cause("resource_too_long")
            if not allowed_resources(self.client).issuperset(granted):
                self.logger.info("ID-JAG resource not governed here", resources=granted)
                raise TokenError("invalid_grant").with_cause("resource_not_governed")
        self.resolve_resources(request, granted)

    def resolve_id_jag_scopes(self):
        """draft-06 §4.4.1: grant the ID-JAG's scopes this provider has, per RFC 6749 §3.3.
        Without a `scope` claim, the request's `scope` parameter applies (RFC 7521 §4.1);
        TokenRequest.parse has already clamped it."""
        claimed = self.id_jag.get("scope")
        if claimed is None:
            return
        if not isinstance(claimed, str):
            raise TokenError("invalid_grant").with_cause("invalid_scope_claim")
        self.scope = set(claimed.split())
        self.check_scopes()

    def resolve_id_jag_user(self) -> User:
        """The user connected to the issuing source with the ID-JAG's `sub`. Without one,
        the user isn't provisioned here (draft-06 §4.4.3 `access_denied`)."""
        connection = (
            UserOAuthSourceConnection.objects.filter(
                source=self.source, identifier=self.id_jag["sub"], user__is_active=True
            )
            .select_related("user")
            .first()
        )
        if not connection:
            self.logger.info("ID-JAG subject has no connection", source=self.source.slug)
            raise TokenError("access_denied").with_cause("subject_not_provisioned")
        return connection.user
