from dataclasses import fields
from json import loads
from typing import Any
from uuid import UUID

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
from authentik.providers.oauth2.errors import TokenError, TokenExchangeError
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider
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


# Upper bound on nested `act` claims, so repeated exchanges cannot grow tokens unbounded
MAX_ACT_DEPTH = 10


class TokenExchangeTokenRequest(FederatedTokenRequest):

    @property
    def is_id_jag_request(self) -> bool:
        return self.requested_token_type == TOKEN_TYPE_URI_ID_JAG

    def resolve_id_jag_audience(self, request: HttpRequest) -> None:
        """Requesting an ID-JAG is *entirely about* targeting an external authorization
        server, so exactly one `audience` is required. It must be configured on a system
        agent that this provider's application may use, rather than resolved to another
        authentik provider. An optional `resource` must be allow-listed on that agent."""
        audiences = request.POST.getlist("audience")
        # draft-ietf-oauth-identity-assertion-authz-grant-06 §4.3.3: more than one audience
        # is a malformed request, not an unknown target.
        if len(audiences) > 1:
            self.logger.warning("ID-JAG request must not have more than one audience")
            raise TokenExchangeError("invalid_request").with_cause("multiple_audiences")
        if not audiences:
            self.logger.warning("ID-JAG request requires an audience")
            raise TokenExchangeError("invalid_target").with_cause("audience_required")
        try:
            from authentik.enterprise.agents.models import Agent
        except ImportError:
            self.logger.warning("ID-JAG requires the enterprise agents module")
            raise TokenExchangeError("invalid_target").with_cause("audience_not_allowed") from None
        target = Agent.objects.filter(
            parent__isnull=True,
            applications__provider=self.provider,
            id_jag_audience=audiences[0],
        ).first()
        if not target:
            self.logger.warning("No system agent for ID-JAG audience", audience=audiences[0])
            raise TokenExchangeError("invalid_target").with_cause("audience_not_allowed")
        resources = request.POST.getlist("resource")
        if len(resources) > 1:
            self.logger.warning("Multiple resources are not supported")
            raise TokenExchangeError("invalid_target").with_cause("multiple_resources")
        if resources and resources[0] not in target.id_jag_resources:
            self.logger.warning("ID-JAG resource not allow-listed", resource=resources[0])
            raise TokenExchangeError("invalid_target").with_cause("resource_not_allowed")
        self.id_jag_audience = audiences[0]
        self.id_jag_agent = target
        self.id_jag_resource = resources[0] if resources else None

    def check_scopes(self):
        """For an ID-JAG, `scope` names scopes of the Resource Authorization Server the
        assertion is for, not this provider's (draft-06 §4.3), so clamping them to this
        provider's scope mappings would silently grant something else. As nothing configures
        which of those scopes may be granted, none are: a request for any is refused with
        invalid_scope rather than silently reduced, and the Resource Authorization Server
        applies its own scope policy for the assertion."""
        if not self.is_id_jag_request:
            return super().check_scopes()
        if self.scope:
            self.logger.warning("Scopes are not supported for ID-JAG requests", scope=self.scope)
            raise TokenExchangeError("invalid_scope").with_cause("id_jag_scope_unsupported")

    def validate_id_token(self, id_token: str) -> FederatedParty | None:
        """An ID token as subject_token (ID-JAG only) must be an ID token this provider
        issued to this client, and the access token it was issued with must still be valid.

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
                audience=self.provider.client_id,
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
        # ExpiringManager drops expired ones, deleted ones are gone.
        # ponytail: unindexed text scan of this provider's tokens, index jti if it gets hot
        for token in AccessToken.objects.filter(
            provider=self.provider, revoked=False, _id_token__contains=jti
        ):
            if token.id_token.jti != jti:
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
        # RFC 8707 resource indicators are not implemented for ordinary token exchange.
        if request.POST.getlist("resource"):
            self.logger.warning("Resource indicators are not supported")
            raise TokenExchangeError("invalid_target").with_cause("target_unsupported")
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
        try:
            if subject_token_type == TOKEN_TYPE_URI_ID_TOKEN:
                federated_party = self.validate_id_token(subject_token)
            else:
                federated_party = self.validate_jwt(subject_token)
        except TokenError:
            if not self.is_id_jag_request:
                raise
            federated_party = None
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
        # Spec's subject_token is normally an ID Token, accepted only when requesting an id-jag
        allowed_subject_token_types = TOKEN_EXCHANGE_TOKEN_TYPES | (
            {TOKEN_TYPE_URI_ID_TOKEN} if self.is_id_jag_request else set()
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
        self.check_policy_access(app, request, oauth_jwt=federated_party.parsed_token)
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
