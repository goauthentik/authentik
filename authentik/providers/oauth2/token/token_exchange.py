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
from authentik.providers.oauth2.token.base_fed import FederatedTokenRequest
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS


class TokenExchangeTokenRequest(FederatedTokenRequest):

    def parse(self, request: HttpRequest) -> None:
        """See https://datatracker.ietf.org/doc/html/rfc8693#section-2.1"""
        super().parse(request)
        # Token targeting is not implemented. RFC 8693 §2.2.2 requires invalid_target when the
        # requested target cannot be honored, so the parameters are refused rather than ignored.
        if request.POST.getlist("audience") or request.POST.getlist("resource"):
            self.logger.warning("Token targeting is not supported")
            raise TokenExchangeError("invalid_target").with_cause("target_unsupported")

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

        self.check_policy_access(app, request, oauth_jwt=federated_party.parsed_token)
        if federated_party.user:
            self.user = federated_party.user
        else:
            self.user = self.create_user_from_jwt(federated_party, app, request)

        self.post_init_token_exchange_actor(request)

        method_args = {
            "jwt": federated_party.parsed_token,
            "subject_token_type": subject_token_type,
            "requested_token_type": self.requested_token_type,
            federated_party.type: federated_party.party,
        }
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
