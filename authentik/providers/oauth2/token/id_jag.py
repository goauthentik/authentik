"""Redeem an ID-JAG (Identity Assertion JWT Authorization Grant) as a Resource Authorization
Server: RFC 7523 jwt-bearer, profiled by draft-ietf-oauth-identity-assertion-authz-grant-06
§4.4. The issuing side (authentik as IdP Authorization Server) lives in token_exchange.py.

Trust is configured with the provider's existing `jwt_federation_sources`: an OAuth source
with an OIDC well-known URL is a trusted IdP Authorization Server. Its issuer identifier is the
one that well-known URL is derived from (draft-06 §7.1, RFC 8414 §3.1, OIDC Discovery §4), and
its signing keys are the source's cached JWKS. The ID-JAG `sub` resolves to the user connected
to that source with the same identifier. Without one, the ID-JAG `email` can connect the one
active user with that address, but only in email domains the source is trusted for (§9.8).
"""

from hashlib import sha256
from hmac import compare_digest
from typing import Any
from urllib.parse import urlparse

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import HttpRequest
from django.utils import timezone
from jwt import PyJWT, PyJWTError

from authentik.common.oauth.constants import JWT_TYPE_ID_JAG
from authentik.core.models import Application, User, UserTypes
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION
from authentik.lib.jwt_mldsa import MLDSA_ALGORITHMS, key_from_jwk
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import ClientType, ScopeMapping
from authentik.providers.oauth2.token.base_fed import FederatedTokenRequest
from authentik.providers.oauth2.utils import is_all_vschar
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
# Clock skew tolerated on exp/iat
ID_JAG_LEEWAY_SECONDS = 30
CACHE_KEY_ID_JAG_JTI = "goauthentik.io/providers/oauth2/id_jag/jti/%s"


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


def is_id_jag_typ(typ: Any) -> bool:
    """RFC 7515 §4.1.9: `typ` is compared case-insensitively, and `application/` may be
    omitted."""
    if not isinstance(typ, str):
        return False
    typ = typ.lower()
    return typ in (JWT_TYPE_ID_JAG, f"application/{JWT_TYPE_ID_JAG}")


class IdJagTokenRequest(FederatedTokenRequest):
    """RFC 7523 jwt-bearer grant, accepting only ID-JAGs (draft-06 §4.4.1)"""

    source: OAuthSource | None = None
    id_jag: dict[str, Any] | None = None
    # Set when the user was found by email; saved once the user is authorized
    new_connection: UserOAuthSourceConnection | None = None

    def check_scopes(self):
        """Scopes come from the ID-JAG; they're resolved once it has been validated."""

    def parse(self, request: HttpRequest) -> None:
        super().parse(request)
        self.authenticate_client()
        assertion = request.POST.get("assertion", "")
        if not assertion:
            raise TokenError("invalid_request").with_cause("missing_assertion")
        self.id_jag = self.validate_id_jag(assertion, request)
        self.resolve_id_jag_resource()
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
        if self.new_connection:
            self.save_new_connection(request)

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
        if self.provider.client_type != ClientType.CONFIDENTIAL:
            raise TokenError("invalid_client").with_cause("public_client")
        if not is_all_vschar(self.client_secret) or not self.provider.client_secret:
            raise TokenError("invalid_client").with_cause("invalid_secret")
        if not compare_digest(self.provider.client_secret, self.client_secret):
            raise TokenError("invalid_client").with_cause("invalid_secret")

    def trusted_source(self, issuer: str) -> OAuthSource | None:
        """The federation source whose well-known URL is derived from `issuer`"""
        candidates = issuer_metadata_urls(issuer)
        if not candidates:
            return None
        for source in self.provider.jwt_federation_sources.filter(
            enabled=True, oidc_well_known_url__in=candidates
        ):
            return source
        return None

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
            self.logger.info("ID-JAG from untrusted issuer", iss=issuer)
            raise TokenError("invalid_grant").with_cause("untrusted_issuer")

        token = self.verify_signature(assertion, source, header)
        # Signature, exp, iat and the required claims are verified; now the profile.
        own_issuer = self.provider.get_issuer(request)
        aud = token["aud"]
        if isinstance(aud, list):
            if len(aud) != 1:
                raise TokenError("invalid_grant").with_cause("invalid_aud")
            aud = aud[0]
        if not own_issuer or aud != own_issuer:
            raise TokenError("invalid_grant").with_cause("invalid_aud")
        if token["client_id"] != self.provider.client_id:
            raise TokenError("invalid_grant").with_cause("client_id_mismatch")
        # Proof of possession (draft-06 §9.11) isn't implemented, so a sender-constrained
        # ID-JAG can't be honoured; accepting it as a bearer grant would drop the binding.
        if "cnf" in token:
            raise TokenError("invalid_grant").with_cause("cnf_unsupported")
        # authentik is a single-tenant Resource Authorization Server (draft-06 §6)
        if "aud_tenant" in token:
            raise TokenError("invalid_grant").with_cause("aud_tenant_unsupported")
        if not isinstance(token["sub"], str) or not token["sub"]:
            raise TokenError("invalid_grant").with_cause("invalid_sub")
        self.check_jti_replay(token)
        self.source = source
        return token

    def verify_signature(
        self, assertion: str, source: OAuthSource, header: dict[str, Any]
    ) -> dict[str, Any]:
        kid = header.get("kid")
        for jwk in source.oidc_jwks.get("keys", []):
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

    def check_jti_replay(self, token: dict[str, Any]):
        """Accept each ID-JAG once (RFC 7523 §3, draft-06 §4.4.4), until it expires"""
        timeout = max(int(token["exp"]) - int(timezone.now().timestamp()), 0)
        timeout += ID_JAG_LEEWAY_SECONDS
        key = sha256(f"{token['iss']}\x00{token['jti']}".encode()).hexdigest()
        with transaction.atomic():
            added = cache.add(CACHE_KEY_ID_JAG_JTI % key, True, timeout=timeout)
        if not added:
            raise TokenError("invalid_grant").with_cause("jti_replayed")

    def resolve_id_jag_resource(self):
        """draft-06 §4.4.1: every `resource` must be governed by this authorization server.
        Providers don't declare governed resources yet (RFC 8707 support), so an ID-JAG
        restricted to resources can't be honoured."""
        if "resource" in self.id_jag:
            raise TokenError("invalid_grant").with_cause("resource_not_governed")

    def resolve_id_jag_scopes(self):
        """draft-06 §4.4.1: grant the ID-JAG's scopes this provider has, per RFC 6749 §3.3.
        Without a `scope` claim, the request's `scope` parameter applies (RFC 7521 §4.1)."""
        claimed = self.id_jag.get("scope")
        if claimed is not None and not isinstance(claimed, str):
            raise TokenError("invalid_grant").with_cause("invalid_scope_claim")
        requested = set(claimed.split()) if claimed is not None else self.scope
        allowed = set(
            ScopeMapping.objects.filter(provider__in=[self.provider]).values_list(
                "scope_name", flat=True
            )
        )
        self.scope = requested & allowed

    def resolve_id_jag_user(self) -> User:
        """Subject resolution (draft-06 §4.4.1, §9.8). `iss` + `sub` is the stable identifier:
        the user connected to the issuing source with the ID-JAG's `sub`. Without one, the
        `email` claim can identify a user who exists here already, as the MCP enterprise-managed
        authorization extension describes, but only in email domains the source is trusted for,
        as an issuer can assert any address. Users aren't created (no JIT provisioning), so an
        unknown subject isn't provisioned here (§4.4.3 `access_denied`)."""
        connection = (
            UserOAuthSourceConnection.objects.filter(
                source=self.source, identifier=self.id_jag["sub"]
            )
            .select_related("user")
            .first()
        )
        if connection:
            if not connection.user.is_active:
                # Never fall back to email: that could hand this subject to another user
                self.logger.info("ID-JAG subject's user is inactive", source=self.source.slug)
                raise TokenError("access_denied").with_cause("subject_inactive")
            return connection.user
        user = self.resolve_id_jag_user_by_email()
        self.new_connection = UserOAuthSourceConnection(
            user=user, source=self.source, identifier=self.id_jag["sub"]
        )
        return user

    def resolve_id_jag_user_by_email(self) -> User:
        """The one active user whose email matches the ID-JAG's, in a trusted domain"""
        email = self.id_jag.get("email")
        trusted_domains = self.source.id_jag_email_domains
        if email is None or not trusted_domains:
            self.logger.info("ID-JAG subject has no connection", source=self.source.slug)
            raise TokenError("access_denied").with_cause("subject_not_provisioned")
        if not isinstance(email, str):
            raise TokenError("invalid_grant").with_cause("invalid_email_claim")
        local, _, domain = email.rpartition("@")
        if not local or domain.lower() not in trusted_domains:
            self.logger.info("ID-JAG email domain isn't trusted", source=self.source.slug)
            raise TokenError("access_denied").with_cause("email_domain_not_trusted")
        # An issuer stating the address isn't verified isn't vouching for it
        if self.id_jag.get("email_verified", True) is not True:
            self.logger.info("ID-JAG email isn't verified", source=self.source.slug)
            raise TokenError("access_denied").with_cause("email_not_verified")
        users = list(
            User.objects.exclude_anonymous()
            .exclude_agents()
            .filter(
                email__iexact=email,
                is_active=True,
                type__in=[UserTypes.INTERNAL, UserTypes.EXTERNAL],
            )[:2]
        )
        if not users:
            self.logger.info("No user with the ID-JAG email", source=self.source.slug)
            raise TokenError("access_denied").with_cause("subject_not_provisioned")
        if len(users) > 1:
            self.logger.warning("Several users have the ID-JAG email", source=self.source.slug)
            raise TokenError("access_denied").with_cause("email_not_unique")
        user = users[0]
        # A user has one connection per source: one for another subject means the email
        # now names someone (or something) else at the issuer
        if UserOAuthSourceConnection.objects.filter(source=self.source, user=user).exists():
            self.logger.warning(
                "User is connected to another ID-JAG subject", source=self.source.slug
            )
            raise TokenError("access_denied").with_cause("subject_conflict")
        return user

    def save_new_connection(self, request: HttpRequest):
        """Connect the user found by email to the ID-JAG subject, so later ID-JAGs resolve by
        `sub`. Saved only once the user is authorized for the application."""
        try:
            with transaction.atomic():
                self.new_connection.save()
        except IntegrityError:
            # A concurrent redemption connected this user first
            raise TokenError("access_denied").with_cause("subject_conflict") from None
        Event.new(
            EventAction.SOURCE_LINKED,
            message="Linked source from an ID-JAG email address",
            source=self.source,
            identifier=self.id_jag["sub"],
        ).from_http(request, user=self.user)
