from dataclasses import fields
from datetime import timedelta
from json import loads
from typing import Any
from uuid import UUID

from django.core.cache import cache
from django.db.models import Q
from django.http import HttpRequest
from jwt import PyJWT, PyJWTError

from authentik.common.oauth.constants import (
    ACTOR_TOKEN_TYPES,
    JWT_TYPE_DPOP_ID_TOKEN,
    TOKEN_EXCHANGE_TOKEN_TYPES,
    TOKEN_TYPE_URI_ACCESS_TOKEN,
    TOKEN_TYPE_URI_AUTHENTIK_TOKEN,
    TOKEN_TYPE_URI_ID_JAG,
    TOKEN_TYPE_URI_ID_TOKEN,
    TOKEN_TYPE_URI_SAML2,
)
from authentik.core.models import Actor, Application, Token, TokenIntents
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION
from authentik.policies.engine import PolicyEngine
from authentik.providers.oauth2.client import OAuthClientContext
from authentik.providers.oauth2.errors import TokenError, TokenExchangeError
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import AccessToken, JWTAlgorithms, OAuth2Provider
from authentik.providers.oauth2.resources import ResourceIndicatorError, parse_resource_indicators
from authentik.providers.oauth2.token.base_fed import FederatedParty, FederatedTokenRequest
from authentik.providers.saml.models import SAMLProvider
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

# `typ` header values an ID token issued by authentik may carry: PyJWT's default `JWT`, or
# `dpop+id_token` for DPoP-bound ID tokens. Anything else (e.g. `at+jwt` or the ID-JAG type)
# explicitly identifies another kind of token.
ID_TOKEN_JWT_TYPES = {"jwt", JWT_TYPE_DPOP_ID_TOKEN}
_ID_TOKEN_FIELDS = frozenset(f.name for f in fields(IDToken))


def issued_id_token_claims(token: AccessToken) -> dict[str, Any]:
    """Claims of the ID token issued alongside `token`, exactly as they were encoded for
    the client. The authorization endpoint (implicit/hybrid) stores them pre-flattened
    (`IDToken.to_dict()`), the token endpoint stores the serialized `IDToken` itself."""
    raw = loads(token._id_token)
    if _ID_TOKEN_FIELDS <= raw.keys() and isinstance(raw.get("claims"), dict):
        return token.id_token.to_dict()
    return {key: value for key, value in raw.items() if value is not None}


# Algorithms an ID-JAG may be signed with. Resource Authorization Servers are only expected to
# accept these (the MCP enterprise-managed authorization profile names ES256 and RS256), and
# an HMAC signature can't be verified by anyone but authentik.
ID_JAG_SIGNING_ALGORITHMS = frozenset({JWTAlgorithms.RS256, JWTAlgorithms.ES256})
# ID-JAGs are short-lived grants (draft-06 §3.1), redeemed right after they're issued; they
# never live longer than this, even when the provider's access tokens do.
ID_JAG_MAX_VALIDITY = timedelta(minutes=5)
# How often an unsupported ID-JAG signing algorithm is reported as a configuration error per
# provider, instead of on every request
ID_JAG_ALG_EVENT_INTERVAL = int(timedelta(hours=1).total_seconds())

# Upper bound on nested `act` claims, so repeated exchanges cannot grow tokens unbounded
MAX_ACT_DEPTH = 10


class TokenExchangeTokenRequest(FederatedTokenRequest):

    @property
    def is_id_jag_request(self) -> bool:
        return self.requested_token_type == TOKEN_TYPE_URI_ID_JAG

    def report_id_jag_signing_alg(self, request: HttpRequest) -> None:
        """Report a provider that can't sign ID-JAGs as a configuration error, at most once
        per ID_JAG_ALG_EVENT_INTERVAL, so that clients retrying can't flood the event log"""
        self.logger.warning("ID-JAG signing algorithm unsupported", alg=self.provider.jwt_alg)
        key = f"goauthentik.io/providers/oauth2/id_jag_alg/{self.provider.pk}"
        if not cache.add(key, True, timeout=ID_JAG_ALG_EVENT_INTERVAL):
            return
        Event.new(
            EventAction.CONFIGURATION_ERROR,
            message=(
                "ID-JAGs require the provider to sign with an RSA or P-256 EC key "
                "(RS256 or ES256)"
            ),
            provider=self.provider,
            alg=self.provider.jwt_alg,
        ).from_http(request)

    def resolve_id_jag_audience(self, request: HttpRequest) -> None:
        """Requesting an ID-JAG is *entirely about* targeting an external authorization
        server, so exactly one `audience` is required. It must be configured on a system
        agent that this provider's application may use, rather than resolved to another
        authentik provider. Requested `resource`s must be allow-listed on that agent."""
        from authentik.enterprise.agents.models import Agent
        from authentik.enterprise.license import LicenseKey

        if self.provider.jwt_alg not in ID_JAG_SIGNING_ALGORITHMS:
            self.report_id_jag_signing_alg(request)
            raise TokenExchangeError("invalid_request").with_cause("id_jag_signing_alg_unsupported")
        # Agents are an enterprise feature
        if not LicenseKey.cached_summary().status.is_valid:
            self.logger.warning("ID-JAG requires a valid enterprise license")
            raise TokenExchangeError("invalid_target").with_cause("enterprise_required")
        audiences = request.POST.getlist("audience")
        # draft-ietf-oauth-identity-assertion-authz-grant-06 §4.3.3: more than one audience
        # is a malformed request, not an unknown target.
        if len(audiences) > 1:
            self.logger.warning("ID-JAG request must not have more than one audience")
            raise TokenExchangeError("invalid_request").with_cause("multiple_audiences")
        # An empty audience is a missing one; it must never match an agent without one
        if not audiences or not audiences[0]:
            self.logger.warning("ID-JAG request requires an audience")
            raise TokenExchangeError("invalid_target").with_cause("audience_required")
        audience = audiences[0]
        targets = list(
            Agent.objects.filter(
                parent__isnull=True,
                applications__provider=self.provider,
                id_jag_audience=audience,
            )[:2]
        )
        if not targets:
            self.logger.warning("No system agent for ID-JAG audience", audience=audience)
            raise TokenExchangeError("invalid_target").with_cause("audience_not_allowed")
        # Agents name the client and resources at the audience, so one must be chosen
        # unambiguously.
        if len(targets) > 1:
            self.logger.warning("Multiple system agents for ID-JAG audience", audience=audience)
            raise TokenExchangeError("invalid_target").with_cause("audience_ambiguous")
        target = targets[0]
        # draft-06 §3.1/§4.3.1: `resource` may be repeated; each must be a valid resource
        # indicator (RFC 8707 §2) allow-listed on the agent.
        try:
            resources = parse_resource_indicators(self.requested_resources)
        except ResourceIndicatorError as exc:
            raise TokenExchangeError("invalid_target").with_cause(exc.cause) from None
        if not set(target.id_jag_resources).issuperset(resources):
            self.logger.warning("ID-JAG resource not allow-listed", resources=resources)
            raise TokenExchangeError("invalid_target").with_cause("resource_not_allowed")
        self.id_jag_audience = audience
        self.id_jag_agent = target
        self.id_jag_resources = resources

    def check_subject_policy_access(
        self, app: Application, request: HttpRequest, federated_party: FederatedParty
    ) -> None:
        """Check that the subject may use the requesting application, and for an ID-JAG,
        that they may get one for the requested audience"""
        if not self.is_id_jag_request:
            return self.check_policy_access(app, request, oauth_jwt=federated_party.parsed_token)
        try:
            self.check_policy_access(app, request, oauth_jwt=federated_party.parsed_token)
        except TokenError:
            # draft-06 §4.3.4.3: a user the IdP won't issue an ID-JAG for is access_denied
            raise TokenExchangeError("access_denied").with_cause(
                "application_access_denied"
            ) from None
        self.check_id_jag_policy_access(request)

    def check_id_jag_policy_access(self, request: HttpRequest) -> None:
        """draft-06 §4.3.4.3: the IdP decides whether the user may get an ID-JAG for the
        audience. That's up to the policies bound to the agent the audience is configured
        on; whether the application may use the client at all is up to its own policies."""
        target = getattr(self.id_jag_agent, "policy_target", None)
        if target is None:
            return
        engine = PolicyEngine(target, self.user, request)
        engine.use_cache = False
        engine.request.context["oauth_scopes"] = self.scope
        engine.request.context["oauth_grant_type"] = self.grant_type
        engine.request.context["oauth_audience"] = self.id_jag_audience
        engine.request.context["oauth_resources"] = list(self.id_jag_resources)
        engine.build()
        if not engine.result.passing:
            self.logger.info(
                "User may not obtain an ID-JAG for audience",
                user=self.user,
                audience=self.id_jag_audience,
            )
            raise TokenExchangeError("access_denied").with_cause("audience_access_denied")

    def validate_id_token(self, id_token: str) -> FederatedParty | None:
        """An ID token as subject_token (ID-JAG only) must be an ID token this provider
        issued to this client, and the grant it was issued with must still be valid.

        Access tokens are signed by the same key, carry the same `jti`/`aud` and have no
        distinguishing `typ`, so a valid signature is not enough to know the token's purpose
        (draft-06 §4.3.3). The verified claims must therefore be exactly those of the ID
        token stored for that `jti`, which access tokens (adding `azp`, a random `uid` and
        `scope`) never are."""
        key, alg = self.provider.jwt_key
        try:
            decoded = PyJWT().decode_complete(
                id_token,
                key if isinstance(key, str) else key.public_key(),
                algorithms=[alg],
                audience=self.client.client_id,
            )
        except (PyJWTError, ValueError, TypeError, AttributeError) as exc:
            self.logger.warning("failed to verify ID token", exc=exc)
            return None
        typ = decoded["header"].get("typ")
        if typ is not None and str(typ).lower() not in ID_TOKEN_JWT_TYPES:
            self.logger.warning("subject_token is not an ID token", typ=typ)
            return None
        claims = decoded["payload"]
        jti = claims.get("jti")
        if not jti or not isinstance(jti, str):
            return None
        # The ID token's jti is stored with the access token it was issued alongside;
        # ExpiringManager drops expired ones, deleted ones are gone. The jti isn't indexed:
        # this is a substring scan of the serialized ID tokens of this client's live access
        # tokens, narrowed first by the indexed client binding. ID-JAG requests are rare
        # compared to token issuance, so this is cheaper than indexing every token's jti.
        for token in AccessToken.objects.filter(
            AccessToken.bound_to_q(self.client), revoked=False, _id_token__contains=jti
        ):
            if token.id_token.jti != jti or not token.is_bound_to(self.client):
                continue
            if claims != issued_id_token_claims(token):
                self.logger.warning("subject_token is not the ID token issued for its jti")
                return None
            return FederatedParty(parsed_token=claims, party=self.provider, user=token.user)
        return None

    def resolve_saml_audience(self, audiences: list[str]) -> None:
        """A SAML Response is requested for the SAML provider whose application's `slug` or
        `pbm_uuid` is the `audience`, which must federate with the requesting provider."""
        if len(audiences) != 1 or not audiences[0]:
            self.logger.warning("SAML token exchange requires exactly one audience")
            raise TokenExchangeError("invalid_target").with_cause("saml_audience_required")
        audience = audiences[0]
        query = Q(application__slug=audience)
        try:
            query |= Q(application__pbm_uuid=UUID(audience))
        except ValueError:
            # Audience is not a UUID; keep slug-only lookup.
            pass
        target = SAMLProvider.objects.filter(query).first()
        if not target:
            self.logger.warning("Audience does not match any provider", audience=audience)
            raise TokenExchangeError("invalid_target").with_cause("unknown_target")
        if not target.jwt_federation_providers.filter(pk=self.provider.pk).exists():
            self.logger.warning("Audience does not federate with the requesting provider")
            raise TokenExchangeError("invalid_target").with_cause("target_not_federated")
        self.saml_provider = target

    def resolve_audience(self, request: HttpRequest) -> None:
        """RFC 8693 §2.1 `audience`: the provider the issued token is for, named by its
        `client_id` or by its application's `pbm_uuid`. Targets that cannot be honored are
        refused with invalid_target (§2.2.2) rather than ignored."""
        if self.is_id_jag_request:
            return self.resolve_id_jag_audience(request)
        audiences = request.POST.getlist("audience")
        if request.POST.get("requested_token_type") == TOKEN_TYPE_URI_SAML2:
            return self.resolve_saml_audience(audiences)
        if not audiences:
            return
        # Multi-provider tokens are not supported.
        if len(audiences) > 1:
            self.logger.warning("Multiple audiences are not supported")
            raise TokenExchangeError("invalid_target").with_cause("multiple_audiences")
        audience = audiences[0]
        target = OAuth2Provider.objects.filter(client_id=audience).first()
        if not target:
            try:
                pbm_uuid = UUID(audience)
            except ValueError:
                pbm_uuid = None
            if pbm_uuid:
                target = OAuth2Provider.objects.filter(application__pbm_uuid=pbm_uuid).first()
        if not target:
            self.logger.warning("Audience does not match any provider", audience=audience)
            raise TokenExchangeError("invalid_target").with_cause("unknown_target")
        # Targeting itself is the default behavior, nothing to switch to.
        if target.pk == self.provider.pk:
            return
        # The target must explicitly federate with the requesting provider.
        if not target.jwt_federation_providers.filter(pk=self.provider.pk).exists():
            self.logger.warning("Audience does not federate with the requesting provider")
            raise TokenExchangeError("invalid_target").with_cause("target_not_federated")
        self.audience_provider = target

    def verify_subject_token(self, subject_token: str, subject_token_type: str) -> FederatedParty:
        """Verify `subject_token` as the type it is declared to be"""
        if self.is_id_jag_request:
            federated_party = self.validate_id_token(subject_token)
        else:
            federated_party = self.validate_jwt(subject_token)
        if not federated_party:
            # Expiry is enforced by PyJWT during signature verification, so an expired
            # subject token also lands here.
            self.logger.warning("No subject token could be verified")
            # RFC 8693 §2.2.2 (profiled by draft-06 §4.3.4.3 for ID-JAG): a subject token
            # that fails validation is invalid_request. Other exchanges keep invalid_grant.
            error = "invalid_request" if self.is_id_jag_request else "invalid_grant"
            raise TokenExchangeError(error).with_cause("subject_token_not_verified")
        return federated_party

    def parse(self, request: HttpRequest) -> None:
        """See https://datatracker.ietf.org/doc/html/rfc8693#section-2.1"""
        super().parse(request)
        subject_token = request.POST.get("subject_token", "")
        subject_token_type = request.POST.get("subject_token_type", "")
        if not subject_token or not subject_token_type:
            self.logger.warning("Missing subject_token or subject_token_type")
            raise TokenExchangeError("invalid_request").with_cause("missing_subject_token")
        # draft-06 §4.3.3: an ID-JAG is requested with an ID token only, which no other
        # exchange accepts
        allowed_subject_token_types = (
            {TOKEN_TYPE_URI_ID_TOKEN} if self.is_id_jag_request else TOKEN_EXCHANGE_TOKEN_TYPES
        )
        if subject_token_type not in allowed_subject_token_types:
            self.logger.warning("Unsupported subject token type", token_type=subject_token_type)
            raise TokenExchangeError("invalid_request").with_cause("unsupported_subject_token_type")
        if self.requested_token_type is None:
            self.requested_token_type = TOKEN_TYPE_URI_ACCESS_TOKEN
        if self.requested_token_type not in TOKEN_EXCHANGE_TOKEN_TYPES | {
            TOKEN_TYPE_URI_ID_JAG,
            TOKEN_TYPE_URI_SAML2,
        }:
            self.logger.warning(
                "Unsupported requested token type", token_type=self.requested_token_type
            )
            raise TokenExchangeError("invalid_request").with_cause(
                "unsupported_requested_token_type"
            )

        federated_party = self.verify_subject_token(subject_token, subject_token_type)

        app = Application.objects.filter(provider=self.provider).first()
        if not app or not app.provider:
            self.logger.info("token_exchange grant for provider without application")
            raise TokenExchangeError("invalid_grant").with_cause("provider_without_application")

        if federated_party.user:
            self.user = federated_party.user
        self.check_subject_policy_access(app, request, federated_party)
        if not federated_party.user:
            self.user = self.create_user_from_jwt(federated_party, app, request)

        if self.audience_provider:
            # An application is also required to give the issued token an `iss`
            target_app = Application.objects.filter(provider=self.audience_provider).first()
            if not target_app:
                self.logger.info("Audience provider has no application")
                raise TokenExchangeError("invalid_target").with_cause("target_without_application")
            self.check_policy_access(target_app, request, oauth_jwt=federated_party.parsed_token)
        if self.saml_provider:
            self.check_policy_access(
                self.saml_provider.application, request, oauth_jwt=federated_party.parsed_token
            )

        self.resolve_exchange_resources(request)

        self.prior_act = self.validate_prior_act(federated_party.parsed_token.get("act"))
        self.post_init_token_exchange_actor(request)
        self.set_id_jag_actor()

        method_args = {
            "jwt": federated_party.parsed_token,
            "subject_token_type": subject_token_type,
            "requested_token_type": self.requested_token_type,
            federated_party.type: federated_party.party,
        }
        if self.audience_provider:
            method_args["audience"] = self.audience_provider.client_id
        if self.id_jag_audience:
            method_args["audience"] = self.id_jag_audience
        if self.saml_provider:
            method_args["audience"] = str(self.saml_provider.application.pbm_uuid)
        # The validated delegation chain the subject token carried; the new actor (if any)
        # is recorded as the event's user.
        if self.prior_act:
            method_args["act"] = self.prior_act
        # A delegated exchange is performed by the actor, so attribute the event to it; the
        # audit log then records it as an agent acting on behalf of the verified subject,
        # matching how direct API calls by an actor are attributed.
        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "token_exchange",
                PLAN_CONTEXT_METHOD_ARGS: method_args,
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=self.actor or self.user)

    def resolve_exchange_resources(self, request: HttpRequest) -> None:
        """RFC 8707 `resource`: restrict the issued access token to the requested resources,
        which the provider the token is issued on must allow. They are refused for SAML
        responses, which have no use for them. ID-JAG requests check `resource` against the
        agent's allow-list instead."""
        if self.is_id_jag_request:
            return
        if self.saml_provider:
            if self.requested_resources:
                self.logger.warning("Resource indicators are not supported for SAML responses")
                raise TokenExchangeError("invalid_target").with_cause("target_unsupported")
            return
        client = (
            OAuthClientContext.for_provider(self.audience_provider)
            if self.audience_provider
            else self.client
        )
        self.resolve_resources(request, client=client)

    def set_id_jag_actor(self) -> None:
        """Bind an ID-JAG to its configured system agent after actor-token validation."""
        if self.is_id_jag_request:
            # ID-JAGs are minted for system agents only, found through the audience above
            if self.actor:
                self.logger.warning("actor_token is not supported for ID-JAG requests")
                raise TokenExchangeError("invalid_request").with_cause("actor_token_unsupported")
            self.actor = self.id_jag_agent

    def validate_prior_act(self, act: Any, depth: int = 0) -> dict | None:
        """RFC 8693 §4.1: validate the delegation chain the verified subject_token carries
        in its `act` claim. Only `sub`, `iss` and a nested `act` are kept; other claims are
        not meaningful for delegation (§4.1) and are dropped."""
        if act is None:
            return None
        if depth >= MAX_ACT_DEPTH:
            self.logger.warning("Subject token delegation chain is too deep")
            raise TokenExchangeError("invalid_grant").with_cause("act_chain_too_deep")
        if not isinstance(act, dict) or not isinstance(act.get("sub"), str):
            self.logger.warning("Subject token has a malformed act claim")
            raise TokenExchangeError("invalid_grant").with_cause("invalid_act_claim")
        valid = {"sub": act["sub"]}
        if "iss" in act:
            if not isinstance(act["iss"], str):
                self.logger.warning("Subject token has a malformed act claim")
                raise TokenExchangeError("invalid_grant").with_cause("invalid_act_claim")
            valid["iss"] = act["iss"]
        if "act" in act:
            valid["act"] = self.validate_prior_act(act["act"], depth + 1)
        return valid

    def post_init_token_exchange_actor(self, request: HttpRequest):
        """RFC 8693 §4.1 delegation: validate an optional `actor_token`, identifying who
        is actually exercising the resulting token (e.g. an Actor acting for the
        verified subject_token's human).

        Actors without an owner (`parent=None`) may only be used via a JWT actor_token.
        Actors with an owner may be used via a JWT *or* an authentik built-in Token,
        but only by the human that owns them (`actor.parent_id == self.user.pk`)."""
        actor_token = request.POST.get("actor_token", "")
        actor_token_type = request.POST.get("actor_token_type", "")
        if not actor_token and not actor_token_type:
            return
        if not actor_token or not actor_token_type:
            self.logger.warning("Missing actor_token or actor_token_type")
            raise TokenExchangeError("invalid_request").with_cause("missing_actor_token")
        if actor_token_type not in ACTOR_TOKEN_TYPES:
            self.logger.warning("Unsupported actor token type", token_type=actor_token_type)
            raise TokenExchangeError("invalid_request").with_cause("unsupported_actor_token_type")

        if actor_token_type == TOKEN_TYPE_URI_AUTHENTIK_TOKEN:
            # Built-in tokens: only valid for actors with an owner -- same lookup idiom as
            # TokenAuthentication.auth_user_lookup (authentik/api/authentication.py).
            # Token.objects excludes expired tokens by default (ExpiringManager).
            key_token = Token.objects.filter(
                key=actor_token, intent=TokenIntents.INTENT_API
            ).first()
            if not key_token:
                self.logger.warning("Actor token not found")
                raise TokenExchangeError("invalid_grant").with_cause("actor_token_not_verified")
            # Actor.objects excludes expired actors by default (ExpiringManager), so an
            # expired actor_token's user simply won't resolve here.
            actor = Actor.objects.filter(pk=key_token.user_id).first()
            if not actor or actor.parent_id != self.user.pk:
                self.logger.warning("Actor is not controlled by the verified subject")
                raise TokenExchangeError("invalid_grant").with_cause("actor_not_controlled")
        else:
            # TOKEN_TYPE_URI_JWT: verified via the same federation-provider trust used
            # for subject_token.
            # Only the provider-federation path applies -- Actors are authentik-internal
            # service accounts, never externally-sourced identities, so the source/JWKS
            # path (validate_jwt_from_source) does not apply here.
            federated_party = self.validate_jwt_from_provider(actor_token)
            if not federated_party:
                self.logger.warning("Actor token not found")
                raise TokenExchangeError("invalid_grant").with_cause("actor_token_not_verified")
            actor = Actor.objects.filter(pk=federated_party.user.pk).first()
            if not actor:
                self.logger.warning("Actor is not controlled by the verified subject")
                raise TokenExchangeError("invalid_grant").with_cause("actor_not_controlled")
            # Ownerless actors (parent=None) are allowed via JWT with no ownership check;
            # owned actors must still belong to the verified subject.
            if actor.parent_id is not None and actor.parent_id != self.user.pk:
                self.logger.warning("Actor is not controlled by the verified subject")
                raise TokenExchangeError("invalid_grant").with_cause("actor_not_controlled")

        self.actor = actor
