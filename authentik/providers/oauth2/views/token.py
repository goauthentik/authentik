"""authentik OAuth2 Token views"""

from base64 import b64encode
from copy import copy
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_CLIENT_CREDENTIALS,
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_PASSWORD,
    GRANT_TYPE_REFRESH_TOKEN,
    GRANT_TYPE_TOKEN_EXCHANGE,
    JWT_TYPE_DPOP_ID_TOKEN,
    SCOPE_OFFLINE_ACCESS,
    TOKEN_TYPE,
    TOKEN_TYPE_URI_SAML2,
)
from authentik.core.middleware import CTX_AUTH_VIA
from authentik.events.signals import get_login_event
from authentik.lib.tracing import active_tracer
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.client import OAuthClientContext, OAuthClientResolver
from authentik.providers.oauth2.errors import (
    DeviceCodeError,
    TokenError,
    UserAuthError,
)
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    BaseGrantModel,
    OAuth2Provider,
    OAuth2SessionLogin,
    RefreshToken,
)
from authentik.providers.oauth2.token.base import TokenRequest
from authentik.providers.oauth2.token.router import parse_token_request
from authentik.providers.oauth2.utils import (
    TokenResponse,
    cors_allow,
    extract_client_auth,
)
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.authn_request_parser import AuthNRequest

LOGGER = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(View):
    """Generate tokens for clients"""

    provider: OAuth2Provider | None = None
    client: OAuthClientContext | None = None
    params: TokenRequest | None = None
    provider_class = OAuth2Provider

    def get_client_resolver(self) -> OAuthClientResolver:
        """Resolver used to find the client (and its provider) for this request"""
        return OAuthClientResolver.legacy(self.provider_class)

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        cors_allow(self.request, response, self.provider.redirect_uris if self.provider else [])
        return response

    def options(self, request: HttpRequest) -> HttpResponse:
        return TokenResponse({})

    def post(self, request: HttpRequest) -> HttpResponse:
        """Generate tokens for clients"""
        try:
            with active_tracer().start_span(
                op="authentik.providers.oauth2.post.parse",
            ):
                client_id, client_secret = extract_client_auth(request)
                self.client = self.get_client_resolver().resolve(request, client_id)
                if not self.client:
                    LOGGER.warning("OAuth2Provider does not exist", client_id=client_id)
                    raise TokenError("invalid_client")
                self.provider = self.client.provider
                self.params = parse_token_request(request, self.client, client_secret)
                CTX_AUTH_VIA.set("oauth_client_secret")

            with active_tracer().start_span(
                op="authentik.providers.oauth2.post.response",
            ):
                if self.params.grant_type == GRANT_TYPE_AUTHORIZATION_CODE:
                    LOGGER.debug("Converting authorization code to access token")
                    return TokenResponse(self.create_code_response())
                if self.params.grant_type == GRANT_TYPE_REFRESH_TOKEN:
                    LOGGER.debug("Refreshing refresh token")
                    return TokenResponse(self.create_refresh_response())
                if self.params.grant_type in [GRANT_TYPE_CLIENT_CREDENTIALS, GRANT_TYPE_PASSWORD]:
                    LOGGER.debug("Client credentials/password grant")
                    return TokenResponse(self.create_client_credentials_response())
                if self.params.grant_type == GRANT_TYPE_DEVICE_CODE:
                    LOGGER.debug("Device code grant")
                    return TokenResponse(self.create_device_code_response())
                if self.params.grant_type == GRANT_TYPE_TOKEN_EXCHANGE:
                    LOGGER.debug("Token exchange grant")
                    return TokenResponse(self.create_token_exchange_response())
                raise TokenError("unsupported_grant_type")
        except TokenError as error:
            return TokenResponse(error.create_dict(request), status=400)
        except UserAuthError as error:
            return TokenResponse(error.create_dict(request), status=403)

    def _get_id_token_jwt_type(self) -> str | None:
        """Return dpop+id_token if key binding is active, else None"""
        if self.params.dpop_jwk is not None:
            return JWT_TYPE_DPOP_ID_TOKEN
        return None

    def _add_cnf_to_id_token(self, id_token: IDToken) -> None:
        """Add cnf claim to ID Token when key binding is active"""
        if self.params.dpop_jwk is not None:
            id_token.cnf = {"jwk": self.params.dpop_jwk}

    def _bind_from(self, grant: BaseGrantModel, source: BaseGrantModel) -> None:
        """Bind a grant issued from `source` to the requesting client, keeping the
        redirect URI and resource `source` was authorized for. `source` has been checked
        to be bound to the requesting client while parsing the request."""
        grant.bind_client(self.client, redirect_uri=source.redirect_uri, resource=source.resource)

    def create_code_response(self) -> dict[str, Any]:
        """See https://datatracker.ietf.org/doc/html/rfc6749#section-4.1"""
        now = timezone.now()
        access_token_expiry = now + timedelta_from_string(self.provider.access_token_validity)
        access_token = AccessToken(
            provider=self.provider,
            user=self.params.authorization_code.user,
            expires=access_token_expiry,
            # Keep same scopes as previous token
            scope=self.params.authorization_code.scope,
            auth_time=self.params.authorization_code.auth_time,
            session=self.params.authorization_code.session,
        )
        self._bind_from(access_token, self.params.authorization_code)
        access_id_token = IDToken.new(
            self.provider,
            access_token,
            self.request,
        )
        access_id_token.nonce = self.params.authorization_code.nonce
        self._add_cnf_to_id_token(access_id_token)
        access_token.id_token = access_id_token
        access_token.save()
        OAuth2SessionLogin.record(access_token, access_id_token)

        id_token_jwt_type = self._get_id_token_jwt_type()
        response = {
            "access_token": access_token.token,
            "token_type": TOKEN_TYPE,
            "scope": " ".join(access_token.scope),
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": access_token.id_token.to_jwt(self.provider, jwt_type=id_token_jwt_type),
        }

        if SCOPE_OFFLINE_ACCESS in self.params.authorization_code.scope:
            refresh_token_expiry = now + timedelta_from_string(self.provider.refresh_token_validity)
            refresh_token = RefreshToken(
                user=self.params.authorization_code.user,
                scope=self.params.authorization_code.scope,
                expires=refresh_token_expiry,
                provider=self.provider,
                auth_time=self.params.authorization_code.auth_time,
                session=self.params.authorization_code.session,
                dpop_jkt=self.params.authorization_code.dpop_jkt,
            )
            self._bind_from(refresh_token, self.params.authorization_code)
            id_token = IDToken.new(
                self.provider,
                refresh_token,
                self.request,
            )
            id_token.nonce = self.params.authorization_code.nonce
            id_token.at_hash = access_token.at_hash
            self._add_cnf_to_id_token(id_token)
            refresh_token.id_token = id_token
            refresh_token.save()
            response["refresh_token"] = refresh_token.token

        # Delete old code
        self.params.authorization_code.delete()
        return response

    def create_refresh_response(self) -> dict[str, Any]:
        """See https://datatracker.ietf.org/doc/html/rfc6749#section-6"""
        unauthorized_scopes = set(self.params.scope) - set(self.params.refresh_token.scope)
        if unauthorized_scopes:
            raise TokenError("invalid_scope")
        if SCOPE_OFFLINE_ACCESS not in self.params.scope:
            raise TokenError("invalid_scope")
        now = timezone.now()
        access_token_expiry = now + timedelta_from_string(self.provider.access_token_validity)
        access_token = AccessToken(
            provider=self.provider,
            user=self.params.refresh_token.user,
            expires=access_token_expiry,
            # Keep same scopes as previous token
            scope=self.params.refresh_token.scope,
            auth_time=self.params.refresh_token.auth_time,
            session=self.params.refresh_token.session,
        )
        self._bind_from(access_token, self.params.refresh_token)
        access_id_token = IDToken.new(
            self.provider,
            access_token,
            self.request,
        )
        self._add_cnf_to_id_token(access_id_token)
        access_token.id_token = access_id_token
        access_token.save()
        OAuth2SessionLogin.record(access_token, access_id_token)

        id_token_jwt_type = self._get_id_token_jwt_type()
        response = {
            "access_token": access_token.token,
            "token_type": TOKEN_TYPE,
            "scope": " ".join(access_token.scope),
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": access_token.id_token.to_jwt(self.provider, jwt_type=id_token_jwt_type),
        }

        refresh_token_threshold = timedelta_from_string(self.provider.refresh_token_threshold)
        if (
            refresh_token_threshold.total_seconds() == 0
            or (self.params.refresh_token.expires - now) < refresh_token_threshold
        ):
            refresh_token_expiry = now + timedelta_from_string(self.provider.refresh_token_validity)
            refresh_token = RefreshToken(
                user=self.params.refresh_token.user,
                scope=self.params.refresh_token.scope,
                expires=refresh_token_expiry,
                provider=self.provider,
                auth_time=self.params.refresh_token.auth_time,
                session=self.params.refresh_token.session,
                dpop_jkt=self.params.refresh_token.dpop_jkt,
            )
            self._bind_from(refresh_token, self.params.refresh_token)
            # Successors stay in their predecessor's family. Tokens issued before
            # families were tracked start a new one.
            if self.params.refresh_token.family_id:
                refresh_token.family_id = self.params.refresh_token.family_id
            id_token = IDToken.new(
                self.provider,
                refresh_token,
                self.request,
            )
            id_token.nonce = self.params.refresh_token.id_token.nonce
            id_token.at_hash = access_token.at_hash
            self._add_cnf_to_id_token(id_token)
            refresh_token.id_token = id_token
            refresh_token.save()

            # Mark old token as revoked
            self.params.refresh_token.revoked = True
            self.params.refresh_token.save()
            response["refresh_token"] = refresh_token.token

        return response

    def create_client_credentials_response(self) -> dict[str, Any]:
        """See https://datatracker.ietf.org/doc/html/rfc6749#section-4.4"""
        now = timezone.now()
        access_token_expiry = now + timedelta_from_string(self.provider.access_token_validity)
        access_token = AccessToken(
            provider=self.provider,
            user=self.params.user,
            expires=access_token_expiry,
            scope=self.params.scope,
            auth_time=now,
        )
        access_token.bind_client(self.client)
        access_token.id_token = IDToken.new(
            self.provider,
            access_token,
            self.request,
        )
        access_token.save()
        return {
            "access_token": access_token.token,
            "token_type": TOKEN_TYPE,
            "scope": " ".join(access_token.scope),
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": access_token.id_token.to_jwt(self.provider),
        }

    def create_device_code_response(self) -> dict[str, Any]:
        """See https://datatracker.ietf.org/doc/html/rfc8628"""
        if not self.params.device_code.user:
            raise DeviceCodeError("authorization_pending")
        now = timezone.now()
        access_token_expiry = now + timedelta_from_string(self.provider.access_token_validity)
        auth_event = get_login_event(self.params.device_code.session)
        access_token = AccessToken(
            provider=self.provider,
            user=self.params.device_code.user,
            expires=access_token_expiry,
            scope=self.params.device_code.scope,
            auth_time=auth_event.created if auth_event else now,
            session=self.params.device_code.session,
        )
        access_token.bind_client(self.client, resource=self.params.device_code.resource)
        access_id_token = IDToken.new(
            self.provider,
            access_token,
            self.request,
        )
        self._add_cnf_to_id_token(access_id_token)
        access_token.id_token = access_id_token
        access_token.save()
        OAuth2SessionLogin.record(access_token, access_id_token)

        id_token_jwt_type = self._get_id_token_jwt_type()
        response = {
            "access_token": access_token.token,
            "token_type": TOKEN_TYPE,
            "scope": " ".join(access_token.scope),
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": access_token.id_token.to_jwt(self.provider, jwt_type=id_token_jwt_type),
        }

        if SCOPE_OFFLINE_ACCESS in self.params.device_code.scope:
            refresh_token_expiry = now + timedelta_from_string(self.provider.refresh_token_validity)
            refresh_token = RefreshToken(
                user=self.params.device_code.user,
                scope=self.params.device_code.scope,
                expires=refresh_token_expiry,
                provider=self.provider,
                auth_time=auth_event.created if auth_event else now,
                dpop_jkt=self.params.device_code.dpop_jkt,
            )
            refresh_token.bind_client(self.client, resource=self.params.device_code.resource)
            id_token = IDToken.new(
                self.provider,
                refresh_token,
                self.request,
            )
            id_token.at_hash = access_token.at_hash
            self._add_cnf_to_id_token(id_token)
            refresh_token.id_token = id_token
            refresh_token.save()
            response["refresh_token"] = refresh_token.token

        # Delete device code
        self.params.device_code.delete()
        return response

    def create_saml_token_exchange_response(self) -> dict[str, Any]:
        """IdP-initiated SAML Response for the federated SAML provider, base64-encoded
        like the SAMLResponse form field, so it can be passed on as-is
        (e.g. to AWS STS AssumeRoleWithSAML)."""
        provider = self.params.saml_provider
        request = copy(self.request)
        request.user = self.params.user
        response = AssertionProcessor(provider, request, AuthNRequest()).build_response()
        return {
            "access_token": b64encode(response.encode()).decode(),
            "issued_token_type": TOKEN_TYPE_URI_SAML2,
            # RFC 8693 §2.2.1: the issued token is not an OAuth access token
            "token_type": "N_A",
            "expires_in": int(
                timedelta_from_string(provider.assertion_valid_not_on_or_after).total_seconds()
            ),
        }

    def create_token_exchange_response(self) -> dict[str, Any]:
        """See https://datatracker.ietf.org/doc/html/rfc8693#section-2.2.1"""
        if self.params.saml_provider:
            return self.create_saml_token_exchange_response()
        # Issued on the `audience` target, else on the client's own provider
        provider = self.params.token_provider
        now = timezone.now()
        access_token_expiry = now + timedelta_from_string(provider.access_token_validity)
        access_token = AccessToken(
            provider=provider,
            user=self.params.user,
            actor=self.params.actor,
            expires=access_token_expiry,
            scope=self.params.scope,
            auth_time=now,
        )
        # A token issued on another provider (`audience`) is issued as that provider's
        # registered client, as it always has been
        access_token.bind_client(
            self.client if provider == self.provider else OAuthClientContext.for_provider(provider)
        )
        access_token.id_token = IDToken.new(
            provider,
            access_token,
            self.request,
            act=self.params.prior_act,
        )
        access_token.save()

        return {
            "access_token": access_token.token,
            # Access tokens are themselves JWTs, so the issued token satisfies either
            # identifier the client may have requested.
            "issued_token_type": self.params.requested_token_type,
            "token_type": TOKEN_TYPE,
            "scope": " ".join(access_token.scope),
            "expires_in": int(
                timedelta_from_string(provider.access_token_validity).total_seconds()
            ),
        }
