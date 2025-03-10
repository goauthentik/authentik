"""authentik OAuth2 Token views"""

from base64 import b64decode, urlsafe_b64encode
from binascii import Error
from dataclasses import InitVar, dataclass
from datetime import datetime
from hashlib import sha256
from re import error as RegexError
from re import fullmatch
from typing import Any
from urllib.parse import urlparse

from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from guardian.shortcuts import get_anonymous_user
from jwt import PyJWK, PyJWT, PyJWTError, decode
from sentry_sdk import start_span
from structlog.stdlib import get_logger

from authentik.core.middleware import CTX_AUTH_VIA
from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    USER_PATH_SYSTEM_PREFIX,
    Application,
    Token,
    TokenIntents,
    User,
    UserTypes,
)
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.events.signals import get_login_event
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.engine import PolicyEngine
from authentik.providers.oauth2.constants import (
    CLIENT_ASSERTION,
    CLIENT_ASSERTION_TYPE,
    CLIENT_ASSERTION_TYPE_JWT,
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_CLIENT_CREDENTIALS,
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_PASSWORD,
    GRANT_TYPE_REFRESH_TOKEN,
    PKCE_METHOD_S256,
    SCOPE_OFFLINE_ACCESS,
    TOKEN_TYPE,
)
from authentik.providers.oauth2.errors import DeviceCodeError, TokenError, UserAuthError
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientTypes,
    DeviceToken,
    OAuth2Provider,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
)
from authentik.providers.oauth2.utils import TokenResponse, cors_allow, extract_client_auth
from authentik.providers.oauth2.views.authorize import FORBIDDEN_URI_SCHEMES
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

LOGGER = get_logger()


@dataclass(slots=True)
class TokenParams:
    """Token params"""

    client_id: str
    client_secret: str
    redirect_uri: str
    grant_type: str
    state: str
    scope: set[str]

    provider: OAuth2Provider

    authorization_code: AuthorizationCode | None = None
    refresh_token: RefreshToken | None = None
    device_code: DeviceToken | None = None
    user: User | None = None

    code_verifier: str | None = None

    raw_code: InitVar[str] = ""
    raw_token: InitVar[str] = ""
    request: InitVar[HttpRequest | None] = None

    @staticmethod
    def parse(
        request: HttpRequest,
        provider: OAuth2Provider,
        client_id: str,
        client_secret: str,
    ) -> "TokenParams":
        """Parse params for request"""
        return TokenParams(
            # Init vars
            raw_code=request.POST.get("code", ""),
            raw_token=request.POST.get("refresh_token", ""),
            request=request,
            # Regular params
            provider=provider,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=request.POST.get("redirect_uri", ""),
            grant_type=request.POST.get("grant_type", ""),
            state=request.POST.get("state", ""),
            scope=set(request.POST.get("scope", "").split()),
            # PKCE parameter.
            code_verifier=request.POST.get("code_verifier"),
        )

    def __check_scopes(self):
        allowed_scope_names = set(
            ScopeMapping.objects.filter(provider__in=[self.provider]).values_list(
                "scope_name", flat=True
            )
        )
        scopes_to_check = self.scope
        if not scopes_to_check.issubset(allowed_scope_names):
            LOGGER.info(
                "Application requested scopes not configured, setting to overlap",
                scope_allowed=allowed_scope_names,
                scope_given=self.scope,
            )
            self.scope = self.scope.intersection(allowed_scope_names)

    def __check_policy_access(self, app: Application, request: HttpRequest, **kwargs):
        with start_span(
            op="authentik.providers.oauth2.token.policy",
        ):
            user = self.user if self.user else get_anonymous_user()
            engine = PolicyEngine(app, user, request)
            # Don't cache as for client_credentials flows the user will not be set
            # so we'll get generic cache results
            engine.use_cache = False
            engine.request.context["oauth_scopes"] = self.scope
            engine.request.context["oauth_grant_type"] = self.grant_type
            engine.request.context["oauth_code_verifier"] = self.code_verifier
            engine.request.context.update(kwargs)
            engine.build()
            result = engine.result
            if not result.passing:
                LOGGER.info(
                    "User not authenticated for application", user=self.user, app_slug=app.slug
                )
                raise TokenError("invalid_grant")

    def __post_init__(self, raw_code: str, raw_token: str, request: HttpRequest):
        if self.grant_type in [GRANT_TYPE_AUTHORIZATION_CODE, GRANT_TYPE_REFRESH_TOKEN]:
            if (
                self.provider.client_type == ClientTypes.CONFIDENTIAL
                and self.provider.client_secret != self.client_secret
            ):
                LOGGER.warning(
                    "Invalid client secret",
                    client_id=self.provider.client_id,
                )
                raise TokenError("invalid_client")
        self.__check_scopes()
        if self.grant_type == GRANT_TYPE_AUTHORIZATION_CODE:
            with start_span(
                op="authentik.providers.oauth2.post.parse.code",
            ):
                self.__post_init_code(raw_code, request)
        elif self.grant_type == GRANT_TYPE_REFRESH_TOKEN:
            with start_span(
                op="authentik.providers.oauth2.post.parse.refresh",
            ):
                self.__post_init_refresh(raw_token, request)
        elif self.grant_type in [GRANT_TYPE_CLIENT_CREDENTIALS, GRANT_TYPE_PASSWORD]:
            with start_span(
                op="authentik.providers.oauth2.post.parse.client_credentials",
            ):
                self.__post_init_client_credentials(request)
        elif self.grant_type == GRANT_TYPE_DEVICE_CODE:
            with start_span(
                op="authentik.providers.oauth2.post.parse.device_code",
            ):
                self.__post_init_device_code(request)
        else:
            LOGGER.warning("Invalid grant type", grant_type=self.grant_type)
            raise TokenError("unsupported_grant_type")

    def __post_init_code(self, raw_code: str, request: HttpRequest):
        if not raw_code:
            LOGGER.warning("Missing authorization code")
            raise TokenError("invalid_grant")

        self.__check_redirect_uri(request)

        self.authorization_code = AuthorizationCode.objects.filter(code=raw_code).first()
        if not self.authorization_code:
            LOGGER.warning("Code does not exist", code=raw_code)
            raise TokenError("invalid_grant")

        if self.authorization_code.is_expired:
            LOGGER.warning(
                "Code is expired",
                token=raw_code,
            )
            raise TokenError("invalid_grant")

        if self.authorization_code.provider != self.provider or self.authorization_code.is_expired:
            LOGGER.warning("Invalid code: invalid client or code has expired")
            raise TokenError("invalid_grant")

        # Validate PKCE parameters.
        if self.authorization_code.code_challenge:
            # Authorization code had PKCE but we didn't get one
            if not self.code_verifier:
                raise TokenError("invalid_grant")
            if self.authorization_code.code_challenge_method == PKCE_METHOD_S256:
                new_code_challenge = (
                    urlsafe_b64encode(sha256(self.code_verifier.encode("ascii")).digest())
                    .decode("utf-8")
                    .replace("=", "")
                )
            else:
                new_code_challenge = self.code_verifier

            if new_code_challenge != self.authorization_code.code_challenge:
                LOGGER.warning("Code challenge not matching")
                raise TokenError("invalid_grant")
        # Token request had a code_verifier but code did not have a code challenge
        # Prevent downgrade
        if not self.authorization_code.code_challenge and self.code_verifier:
            raise TokenError("invalid_grant")

    def __check_redirect_uri(self, request: HttpRequest):
        allowed_redirect_urls = self.provider.redirect_uris
        # At this point, no provider should have a blank redirect_uri, in case they do
        # this will check an empty array and raise an error

        match_found = False
        for allowed in allowed_redirect_urls:
            if allowed.matching_mode == RedirectURIMatchingMode.STRICT:
                if self.redirect_uri == allowed.url:
                    match_found = True
                    break
            if allowed.matching_mode == RedirectURIMatchingMode.REGEX:
                try:
                    if fullmatch(allowed.url, self.redirect_uri):
                        match_found = True
                        break
                except RegexError as exc:
                    LOGGER.warning(
                        "Failed to parse regular expression",
                        exc=exc,
                        url=allowed.url,
                        provider=self.provider,
                    )
                    Event.new(
                        EventAction.CONFIGURATION_ERROR,
                        message="Invalid redirect_uri configured",
                        provider=self.provider,
                    ).from_http(request)
        if not match_found:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message="Invalid redirect URI used by provider",
                provider=self.provider,
                redirect_uri=self.redirect_uri,
                expected=allowed_redirect_urls,
            ).from_http(request)
            raise TokenError("invalid_client")

        # Check against forbidden schemes
        if urlparse(self.redirect_uri).scheme in FORBIDDEN_URI_SCHEMES:
            raise TokenError("invalid_request")

    def __post_init_refresh(self, raw_token: str, request: HttpRequest):
        if not raw_token:
            LOGGER.warning("Missing refresh token")
            raise TokenError("invalid_grant")

        self.refresh_token = RefreshToken.objects.filter(
            token=raw_token, provider=self.provider
        ).first()
        if not self.refresh_token:
            LOGGER.warning(
                "Refresh token does not exist",
                token=raw_token,
            )
            raise TokenError("invalid_grant")
        if self.refresh_token.is_expired:
            LOGGER.warning(
                "Refresh token is expired",
                token=raw_token,
            )
            raise TokenError("invalid_grant")
        # https://datatracker.ietf.org/doc/html/rfc6749#section-6
        # Fallback to original token's scopes when none are given
        if not self.scope:
            self.scope = self.refresh_token.scope
        if self.refresh_token.revoked:
            LOGGER.warning("Refresh token is revoked", token=raw_token)
            Event.new(
                action=EventAction.SUSPICIOUS_REQUEST,
                message="Revoked refresh token was used",
                token=self.refresh_token,
                provider=self.refresh_token.provider,
            ).from_http(request, user=self.refresh_token.user)
            raise TokenError("invalid_grant")

    def __post_init_client_credentials(self, request: HttpRequest):
        # client_credentials flow with client assertion
        if request.POST.get(CLIENT_ASSERTION_TYPE, "") != "":
            return self.__post_init_client_credentials_jwt(request)
        # authentik-custom-ish client credentials flow
        if request.POST.get("username", "") != "":
            return self.__post_init_client_credentials_creds(
                request, request.POST.get("username"), request.POST.get("password")
            )
        # Standard method which creates an automatic user
        if self.client_secret == self.provider.client_secret:
            return self.__post_init_client_credentials_generated(request)
        # Standard workaround method which stores username:password
        # as client_secret
        try:
            user, _, password = b64decode(self.client_secret).decode("utf-8").partition(":")
            return self.__post_init_client_credentials_creds(request, user, password)
        except (ValueError, Error):
            raise TokenError("invalid_grant") from None

    def __post_init_client_credentials_creds(
        self, request: HttpRequest, username: str, password: str
    ):
        # Authenticate user based on credentials
        user = User.objects.filter(username=username).first()
        if not user:
            raise TokenError("invalid_grant")
        token: Token = Token.filter_not_expired(
            key=password, intent=TokenIntents.INTENT_APP_PASSWORD
        ).first()
        if not token or token.user.uid != user.uid:
            raise TokenError("invalid_grant")
        self.user = user
        # Authorize user access
        app = Application.objects.filter(provider=self.provider).first()
        if not app or not app.provider:
            raise TokenError("invalid_grant")
        self.__check_policy_access(app, request)

        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "token",
                PLAN_CONTEXT_METHOD_ARGS: {
                    "identifier": token.identifier,
                },
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=user)

    def __validate_jwt_from_source(
        self, assertion: str
    ) -> tuple[dict, OAuthSource] | tuple[None, None]:
        # Fully decode the JWT without verifying the signature, so we can get access to
        # the header.
        # Get the Key ID from the header, and use that to optimise our source query to only find
        # sources that have a JWK for that Key ID
        # The Key ID doesn't have a fixed format, but must match between an issued JWT
        # and whatever is returned by the JWKS endpoint
        try:
            decode_unvalidated = PyJWT().decode_complete(
                assertion, options={"verify_signature": False}
            )
        except (PyJWTError, ValueError, TypeError, AttributeError) as exc:
            LOGGER.warning("failed to parse JWT for kid lookup", exc=exc)
            raise TokenError("invalid_grant") from None
        expected_kid = decode_unvalidated["header"]["kid"]
        fallback_alg = decode_unvalidated["header"]["alg"]
        token = source = None
        for source in self.provider.jwt_federation_sources.filter(
            oidc_jwks__keys__contains=[{"kid": expected_kid}]
        ):
            LOGGER.debug("verifying JWT with source", source=source.slug)
            keys = source.oidc_jwks.get("keys", [])
            for key in keys:
                if key.get("kid") and key.get("kid") != expected_kid:
                    continue
                LOGGER.debug("verifying JWT with key", source=source.slug, key=key.get("kid"))
                try:
                    parsed_key = PyJWK.from_dict(key).key
                    token = decode(
                        assertion,
                        parsed_key,
                        algorithms=[key.get("alg")] if "alg" in key else [fallback_alg],
                        options={
                            "verify_aud": False,
                        },
                    )
                # AttributeError is raised when the configured JWK is a private key
                # and not a public key
                except (PyJWTError, ValueError, TypeError, AttributeError) as exc:
                    LOGGER.warning("failed to verify JWT", exc=exc, source=source.slug)
        if token:
            LOGGER.info("successfully verified JWT with source", source=source.slug)
        return token, source

    def __validate_jwt_from_provider(
        self, assertion: str
    ) -> tuple[dict, OAuth2Provider] | tuple[None, None]:
        token = provider = _key = None
        federated_token = AccessToken.objects.filter(
            token=assertion, provider__in=self.provider.jwt_federation_providers.all()
        ).first()
        if federated_token:
            _key, _alg = federated_token.provider.jwt_key
            try:
                token = decode(
                    assertion,
                    _key.public_key(),
                    algorithms=[_alg],
                    options={
                        "verify_aud": False,
                    },
                )
                provider = federated_token.provider
                self.user = federated_token.user
            except (PyJWTError, ValueError, TypeError, AttributeError) as exc:
                LOGGER.warning(
                    "failed to verify JWT", exc=exc, provider=federated_token.provider.name
                )

        if token:
            LOGGER.info("successfully verified JWT with provider", provider=provider.name)
        return token, provider

    def __post_init_client_credentials_jwt(self, request: HttpRequest):
        assertion_type = request.POST.get(CLIENT_ASSERTION_TYPE, "")
        if assertion_type != CLIENT_ASSERTION_TYPE_JWT:
            LOGGER.warning("Invalid assertion type", assertion_type=assertion_type)
            raise TokenError("invalid_grant")

        client_secret = request.POST.get("client_secret", None)
        assertion = request.POST.get(CLIENT_ASSERTION, client_secret)
        if not assertion:
            LOGGER.warning("Missing client assertion")
            raise TokenError("invalid_grant")

        source = provider = None

        token, source = self.__validate_jwt_from_source(assertion)
        if not token:
            token, provider = self.__validate_jwt_from_provider(assertion)

        if not token:
            LOGGER.warning("No token could be verified")
            raise TokenError("invalid_grant")

        if "exp" in token:
            exp = datetime.fromtimestamp(token["exp"])
            # Non-timezone aware check since we assume `exp` is in UTC
            if datetime.now() >= exp:
                LOGGER.info("JWT token expired")
                raise TokenError("invalid_grant")

        app = Application.objects.filter(provider=self.provider).first()
        if not app or not app.provider:
            LOGGER.info("client_credentials grant for provider without application")
            raise TokenError("invalid_grant")

        self.__check_policy_access(app, request, oauth_jwt=token)
        if not provider:
            self.__create_user_from_jwt(token, app, source)

        method_args = {
            "jwt": token,
        }
        if source:
            method_args["source"] = source
        if provider:
            method_args["provider"] = provider
        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "jwt",
                PLAN_CONTEXT_METHOD_ARGS: method_args,
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=self.user)

    def __post_init_client_credentials_generated(self, request: HttpRequest):
        # Authorize user access
        app = Application.objects.filter(provider=self.provider).first()
        if not app or not app.provider:
            raise TokenError("invalid_grant")
        with audit_ignore():
            self.user, _ = User.objects.update_or_create(
                # trim username to ensure the entire username is max 150 chars
                # (22 chars being the length of the "template")
                username=f"ak-{self.provider.name[:150-22]}-client_credentials",
                defaults={
                    "last_login": timezone.now(),
                    "name": f"Autogenerated user from application {app.name} (client credentials)",
                    "path": f"{USER_PATH_SYSTEM_PREFIX}/apps/{app.slug}",
                    "type": UserTypes.SERVICE_ACCOUNT,
                },
            )
            self.user.attributes[USER_ATTRIBUTE_GENERATED] = True
            self.user.save()
        self.__check_policy_access(app, request)

        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "oauth_client_secret",
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=self.user)

    def __post_init_device_code(self, request: HttpRequest):
        device_code = request.POST.get("device_code", "")
        code = DeviceToken.objects.filter(device_code=device_code, provider=self.provider).first()
        if not code:
            raise TokenError("invalid_grant")
        self.device_code = code

    def __create_user_from_jwt(self, token: dict[str, Any], app: Application, source: OAuthSource):
        """Create user from JWT"""
        with audit_ignore():
            self.user, created = User.objects.update_or_create(
                username=f"{self.provider.name}-{token.get('sub')}",
                defaults={
                    "last_login": timezone.now(),
                    "name": (
                        f"Autogenerated user from application {app.name} (client credentials JWT)"
                    ),
                    "path": source.get_user_path(),
                    "type": UserTypes.SERVICE_ACCOUNT,
                },
            )
            self.user.attributes[USER_ATTRIBUTE_GENERATED] = True
            self.user.save()
            exp = token.get("exp")
            if created and exp:
                self.user.attributes[USER_ATTRIBUTE_EXPIRES] = exp
                self.user.save()


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(View):
    """Generate tokens for clients"""

    provider: OAuth2Provider | None = None
    params: TokenParams | None = None

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        allowed_origins = []
        if self.provider:
            allowed_origins = [x.url for x in self.provider.redirect_uris]
        cors_allow(self.request, response, *allowed_origins)
        return response

    def options(self, request: HttpRequest) -> HttpResponse:
        return TokenResponse({})

    def post(self, request: HttpRequest) -> HttpResponse:
        """Generate tokens for clients"""
        try:
            with start_span(
                op="authentik.providers.oauth2.post.parse",
            ):
                client_id, client_secret = extract_client_auth(request)
                self.provider = OAuth2Provider.objects.filter(client_id=client_id).first()
                if not self.provider:
                    LOGGER.warning("OAuth2Provider does not exist", client_id=client_id)
                    raise TokenError("invalid_client")
                CTX_AUTH_VIA.set("oauth_client_secret")
                self.params = TokenParams.parse(request, self.provider, client_id, client_secret)

            with start_span(
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
                raise TokenError("unsupported_grant_type")
        except (TokenError, DeviceCodeError) as error:
            return TokenResponse(error.create_dict(), status=400)
        except UserAuthError as error:
            return TokenResponse(error.create_dict(), status=403)

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
        access_id_token = IDToken.new(
            self.provider,
            access_token,
            self.request,
        )
        access_id_token.nonce = self.params.authorization_code.nonce
        access_token.id_token = access_id_token
        access_token.save()

        response = {
            "access_token": access_token.token,
            "token_type": TOKEN_TYPE,
            "scope": " ".join(access_token.scope),
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": access_token.id_token.to_jwt(self.provider),
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
            )
            id_token = IDToken.new(
                self.provider,
                refresh_token,
                self.request,
            )
            id_token.nonce = self.params.authorization_code.nonce
            id_token.at_hash = access_token.at_hash
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
        access_token.id_token = IDToken.new(
            self.provider,
            access_token,
            self.request,
        )
        access_token.save()

        refresh_token_expiry = now + timedelta_from_string(self.provider.refresh_token_validity)
        refresh_token = RefreshToken(
            user=self.params.refresh_token.user,
            scope=self.params.refresh_token.scope,
            expires=refresh_token_expiry,
            provider=self.provider,
            auth_time=self.params.refresh_token.auth_time,
            session=self.params.refresh_token.session,
        )
        id_token = IDToken.new(
            self.provider,
            refresh_token,
            self.request,
        )
        id_token.nonce = self.params.refresh_token.id_token.nonce
        id_token.at_hash = access_token.at_hash
        refresh_token.id_token = id_token
        refresh_token.save()

        # Mark old token as revoked
        self.params.refresh_token.revoked = True
        self.params.refresh_token.save()

        return {
            "access_token": access_token.token,
            "refresh_token": refresh_token.token,
            "token_type": TOKEN_TYPE,
            "scope": " ".join(access_token.scope),
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": access_token.id_token.to_jwt(self.provider),
        }

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
        access_token.id_token = IDToken.new(
            self.provider,
            access_token,
            self.request,
        )
        access_token.save()

        response = {
            "access_token": access_token.token,
            "token_type": TOKEN_TYPE,
            "scope": " ".join(access_token.scope),
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": access_token.id_token.to_jwt(self.provider),
        }

        if SCOPE_OFFLINE_ACCESS in self.params.device_code.scope:
            refresh_token_expiry = now + timedelta_from_string(self.provider.refresh_token_validity)
            refresh_token = RefreshToken(
                user=self.params.device_code.user,
                scope=self.params.device_code.scope,
                expires=refresh_token_expiry,
                provider=self.provider,
                auth_time=auth_event.created if auth_event else now,
            )
            id_token = IDToken.new(
                self.provider,
                refresh_token,
                self.request,
            )
            id_token.at_hash = access_token.at_hash
            refresh_token.id_token = id_token
            refresh_token.save()
            response["refresh_token"] = refresh_token.token

        # Delete device code
        self.params.device_code.delete()
        return response
