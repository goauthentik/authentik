from uuid import UUID

from django.http import HttpRequest

from authentik.common.oauth.constants import (
    ACTOR_TOKEN_TYPES,
    TOKEN_EXCHANGE_TOKEN_TYPES,
    TOKEN_TYPE_URI_ACCESS_TOKEN,
    TOKEN_TYPE_URI_AUTHENTIK_TOKEN,
)
from authentik.core.models import Actor, Application, Token, TokenIntents
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION
from authentik.providers.oauth2.errors import TokenExchangeError
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.token.base_fed import FederatedTokenRequest
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS


class TokenExchangeTokenRequest(FederatedTokenRequest):

    def resolve_audience(self, request: HttpRequest) -> None:
        """RFC 8693 §2.1 `audience`: the provider the issued token is for, named by its
        `client_id` or by its application's `pbm_uuid`. Targets that cannot be honored are
        refused with invalid_target (§2.2.2) rather than ignored."""
        # RFC 8707 resource indicators are not implemented.
        if request.POST.getlist("resource"):
            self.logger.warning("Resource indicators are not supported")
            raise TokenExchangeError("invalid_target").with_cause("target_unsupported")
        audiences = request.POST.getlist("audience")
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

    def parse(self, request: HttpRequest) -> None:
        """See https://datatracker.ietf.org/doc/html/rfc8693#section-2.1"""
        super().parse(request)
        subject_token = request.POST.get("subject_token", "")
        subject_token_type = request.POST.get("subject_token_type", "")
        if not subject_token or not subject_token_type:
            self.logger.warning("Missing subject_token or subject_token_type")
            raise TokenExchangeError("invalid_request").with_cause("missing_subject_token")
        if subject_token_type not in TOKEN_EXCHANGE_TOKEN_TYPES:
            self.logger.warning("Unsupported subject token type", token_type=subject_token_type)
            raise TokenExchangeError("invalid_request").with_cause("unsupported_subject_token_type")
        if self.requested_token_type is None:
            self.requested_token_type = TOKEN_TYPE_URI_ACCESS_TOKEN
        if self.requested_token_type not in TOKEN_EXCHANGE_TOKEN_TYPES:
            self.logger.warning(
                "Unsupported requested token type", token_type=self.requested_token_type
            )
            raise TokenExchangeError("invalid_request").with_cause(
                "unsupported_requested_token_type"
            )

        federated_party = self.validate_jwt(subject_token)

        if not federated_party:
            # Expiry is enforced by PyJWT during signature verification, so an expired
            # subject token also lands here.
            self.logger.warning("No subject token could be verified")
            raise TokenExchangeError("invalid_grant").with_cause("subject_token_not_verified")

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

        self.post_init_token_exchange_actor(request)

        method_args = {
            "jwt": federated_party.parsed_token,
            "subject_token_type": subject_token_type,
            "requested_token_type": self.requested_token_type,
            federated_party.type: federated_party.party,
        }
        if self.audience_provider:
            method_args["audience"] = self.audience_provider.client_id
        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "token_exchange",
                PLAN_CONTEXT_METHOD_ARGS: method_args,
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=self.user)

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
