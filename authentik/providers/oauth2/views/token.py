"""authentik OAuth2 Token views"""
from base64 import urlsafe_b64encode
from dataclasses import InitVar, dataclass
from datetime import datetime
from hashlib import sha256
from re import error as RegexError
from re import fullmatch
from typing import Any, Optional

from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from guardian.shortcuts import get_anonymous_user
from jwt import PyJWK, PyJWT, PyJWTError, decode
from sentry_sdk.hub import Hub
from structlog.stdlib import get_logger

from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    Application,
    Token,
    TokenIntents,
    User,
)
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
    RefreshToken,
)
from authentik.providers.oauth2.utils import TokenResponse, cors_allow, extract_client_auth
from authentik.sources.oauth.models import OAuthSource
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

LOGGER = get_logger()


@dataclass(slots=True)
# pylint: disable=too-many-instance-attributes
class TokenParams:
    """Token params"""

    client_id: str
    client_secret: str
    redirect_uri: str
    grant_type: str
    state: str
    scope: list[str]

    provider: OAuth2Provider

    authorization_code: Optional[AuthorizationCode] = None
    refresh_token: Optional[RefreshToken] = None
    device_code: Optional[DeviceToken] = None
    user: Optional[User] = None

    code_verifier: Optional[str] = None

    raw_code: InitVar[str] = ""
    raw_token: InitVar[str] = ""
    request: InitVar[Optional[HttpRequest]] = None

    @staticmethod
    def parse(
        request: HttpRequest,
        provider: OAuth2Provider,
        client_id: str,
        client_secret: str,
    ) -> "TokenParams":
        """Parse the token parameters from the HTTP request."""
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
            scope=request.POST.get("scope", "").split(),
            # PKCE parameter.
            code_verifier=request.POST.get("code_verifier"),
        )

    def __check_policy_access(self, app: Application, request: HttpRequest, **kwargs):
        """
        Private method to check the policy access for a given application and request.

        Parameters:
            app (Application): The application to check the policy access for.
            request (HttpRequest): The request to check the policy access for.
            **kwargs: Additional keyword arguments.
        """
        with Hub.current.start_span(
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
        """
        Initialize an instance of a class.

        This method is used to initialize an instance of a class. It takes
        four parameters: 'self', 'raw_code', 'raw_token', and 'request'.
        The method checks the 'grant_type' attribute of the instance and performs
        different actions based on its value. If the 'grant_type' is 'authorization_code',
        it calls the '__post_init_code' method and passes the 'raw_code' and 'request'
        parameters. If the 'grant_type' is 'refresh_token', it calls the '__post_init_refresh'
        method and passes the 'raw_token' and 'request' parameters. If the 'grant_type' is
        'client_credentials' or 'password', it calls the '__post_init_client_credentials'
        method and passes the 'request' parameter. If the 'grant_type' is 'device_code',
        it calls the '__post_init_device_code' method and passes the 'request' parameter.
        If the 'grant_type' is none of the above, it raises a 'TokenError' exception
        with the message 'unsupported_grant_type'.
        """
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

        if self.grant_type == GRANT_TYPE_AUTHORIZATION_CODE:
            with Hub.current.start_span(
                op="authentik.providers.oauth2.post.parse.code",
            ):
                self.__post_init_code(raw_code, request)
        elif self.grant_type == GRANT_TYPE_REFRESH_TOKEN:
            with Hub.current.start_span(
                op="authentik.providers.oauth2.post.parse.refresh",
            ):
                self.__post_init_refresh(raw_token, request)
        elif self.grant_type in [GRANT_TYPE_CLIENT_CREDENTIALS, GRANT_TYPE_PASSWORD]:
            with Hub.current.start_span(
                op="authentik.providers.oauth2.post.parse.client_credentials",
            ):
                self.__post_init_client_credentials(request)
        elif self.grant_type == GRANT_TYPE_DEVICE_CODE:
            with Hub.current.start_span(
                op="authentik.providers.oauth2.post.parse.device_code",
            ):
                self.__post_init_device_code(request)
        else:
            LOGGER.warning("Invalid grant type", grant_type=self.grant_type)
            raise TokenError("unsupported_grant_type")

    def __post_init_code(self, raw_code: str, request: HttpRequest):
        """
        Perform various validation checks related to an authorization code.

        This method checks if the provided 'raw_code' is empty and raises a 'TokenError' exception with 'invalid_grant' if it is.
        Then it compares the 'self.redirect_uri' with a list of allowed redirect URLs using regular expressions and raises a 'TokenError' exception with 'invalid_client' if there is no match.
        After that, it tries to find the 'AuthorizationCode' object with the provided 'raw_code' and raises a 'TokenError' exception with 'invalid_grant' if it doesn't exist or if it is expired.
        Finally, it validates PKCE parameters by comparing the 'code_verifier' with the 'code_challenge' of the 'AuthorizationCode' object and raises a 'TokenError' exception with 'invalid_grant' if they don't match.

        Parameters:
            raw_code (str): The raw authorization code.
            request (HttpRequest): The HTTP request object.

        Raises:
            TokenError: If the 'raw_code' is empty, the redirect URI is invalid, the 'AuthorizationCode' object doesn't exist or is expired, or the PKCE parameters don't match.
        """
        if not raw_code:
            LOGGER.warning("Missing authorization code")
            raise TokenError("invalid_grant")

        allowed_redirect_urls = self.provider.redirect_uris.split()
        # At this point, no provider should have a blank redirect_uri, in case they do
        # this will check an empty array and raise an error
        try:
            if not any(fullmatch(x, self.redirect_uri) for x in allowed_redirect_urls):
                LOGGER.warning(
                    "Invalid redirect uri (regex comparison)",
                    redirect_uri=self.redirect_uri,
                    expected=allowed_redirect_urls,
                )
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message="Invalid redirect URI used by provider",
                    provider=self.provider,
                    redirect_uri=self.redirect_uri,
                    expected=allowed_redirect_urls,
                ).from_http(request)
                raise TokenError("invalid_client")
        except RegexError as exc:
            LOGGER.info("Failed to parse regular expression, checking directly", exc=exc)
            if not any(x == self.redirect_uri for x in allowed_redirect_urls):
                LOGGER.warning(
                    "Invalid redirect uri (strict comparison)",
                    redirect_uri=self.redirect_uri,
                    expected=allowed_redirect_urls,
                )
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    message="Invalid redirect_uri configured",
                    provider=self.provider,
                ).from_http(request)
                raise TokenError("invalid_client")

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
        if self.code_verifier:
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

    def __post_init_refresh(self, raw_token: str, request: HttpRequest):
        """
        Refreshes the token with the given raw token and request.

        This method is responsible for refreshing a token. It takes in two parameters:
        - raw_token (str): The raw token to be refreshed.
        - request (HttpRequest): The HTTP request object.

        Raises:
            TokenError: If the raw token is empty or invalid.

        """
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
        """
        Perform post-initialization tasks related to client credentials.

        This method is responsible for performing various tasks related to client credentials. It first checks if the client assertion type is present in the request and if so, calls the __post_init_client_credentials_jwt method. Then, it authenticates the user based on the provided username and password. If the user is not found, it raises a TokenError. It then retrieves a token associated with the provided password and checks if it is still valid and belongs to the authenticated user. If not, it raises a TokenError. Next, it sets the user attribute of the current object to the authenticated user. After that, it retrieves an application object based on the provider attribute of the current object and checks if it exists and has a provider. If not, it raises a TokenError. Finally, it calls the __check_policy_access method to authorize user access and logs a login event. The method does not return any value.

        Parameters:
            request (HttpRequest): The request object containing the client credentials.
        """
        if request.POST.get(CLIENT_ASSERTION_TYPE, "") != "":
            return self.__post_init_client_credentials_jwt(request)
        # Authenticate user based on credentials
        username = request.POST.get("username")
        password = request.POST.get("password")
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
        return None

    # pylint: disable=too-many-locals
    def __post_init_client_credentials_jwt(self, request: HttpRequest):
        """Handles the POST request for client credentials JWT."""
        assertion_type = request.POST.get(CLIENT_ASSERTION_TYPE, "")
        if assertion_type != CLIENT_ASSERTION_TYPE_JWT:
            LOGGER.warning("Invalid assertion type", assertion_type=assertion_type)
            raise TokenError("invalid_grant")

        client_secret = request.POST.get("client_secret", None)
        assertion = request.POST.get(CLIENT_ASSERTION, client_secret)
        if not assertion:
            LOGGER.warning("Missing client assertion")
            raise TokenError("invalid_grant")

        token = None

        source: Optional[OAuthSource] = None
        parsed_key: Optional[PyJWK] = None

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
            raise TokenError("invalid_grant")
        expected_kid = decode_unvalidated["header"]["kid"]
        for source in self.provider.jwks_sources.filter(
            oidc_jwks__keys__contains=[{"kid": expected_kid}]
        ):
            LOGGER.debug("verifying JWT with source", source=source.slug)
            keys = source.oidc_jwks.get("keys", [])
            for key in keys:
                LOGGER.debug("verifying JWT with key", source=source.slug, key=key.get("kid"))
                try:
                    parsed_key = PyJWK.from_dict(key)
                    token = decode(
                        assertion,
                        parsed_key.key,
                        algorithms=[key.get("alg")],
                        options={
                            "verify_aud": False,
                        },
                    )
                # AttributeError is raised when the configured JWK is a private key
                # and not a public key
                except (PyJWTError, ValueError, TypeError, AttributeError) as exc:
                    LOGGER.warning("failed to verify JWT", exc=exc, source=source.slug)

        if not token:
            LOGGER.warning("No token could be verified")
            raise TokenError("invalid_grant")

        LOGGER.info("successfully verified JWT with source", source=source.slug)

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
        self.__create_user_from_jwt(token, app, source)

        method_args = {
            "jwt": token,
        }
        if source:
            method_args["source"] = source
        if parsed_key:
            method_args["jwk_id"] = parsed_key.key_id
        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "jwt",
                PLAN_CONTEXT_METHOD_ARGS: method_args,
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=self.user)

    def __post_init_device_code(self, request: HttpRequest):
        """Initialize the 'device_code' attribute from the request."""
        device_code = request.POST.get("device_code", "")
        code = DeviceToken.objects.filter(device_code=device_code, provider=self.provider).first()
        if not code:
            raise TokenError("invalid_grant")
        self.device_code = code

    def __create_user_from_jwt(self, token: dict[str, Any], app: Application, source: OAuthSource):
        """Create a user from JWT token."""
        exp = token.get("exp")
        self.user, created = User.objects.update_or_create(
            username=f"{self.provider.name}-{token.get('sub')}",
            defaults={
                "attributes": {
                    USER_ATTRIBUTE_GENERATED: True,
                },
                "last_login": timezone.now(),
                "name": f"Autogenerated user from application {app.name} (client credentials JWT)",
                "path": source.get_user_path(),
            },
        )
        if created and exp:
            self.user.attributes[USER_ATTRIBUTE_EXPIRES] = exp
            self.user.save()


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(View):
    """Generate tokens for clients"""

    provider: Optional[OAuth2Provider] = None
    params: Optional[TokenParams] = None

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Dispatches the HTTP request to the appropriate handler.

        This method calls the super().dispatch method to perform the default handling of the request.
        It also adds CORS headers to the response based on the provider's redirect_uris.

        Parameters:
            request (HttpRequest): The HTTP request.
            *args: Additional positional arguments for the handler.
            **kwargs: Additional keyword arguments for the handler.

        Returns:
            HttpResponse: The HTTP response.
        """
        response = super().dispatch(request, *args, **kwargs)
        allowed_origins = []
        if self.provider:
            allowed_origins = self.provider.redirect_uris.split("\n")
        cors_allow(self.request, response, *allowed_origins)
        return response

    def options(self, request: HttpRequest) -> HttpResponse:
        """
        Handles the OPTIONS HTTP request.

        This method returns an empty response.

        Parameters:
            request (HttpRequest): The HTTP request.

        Returns:
            HttpResponse: The HTTP response.
        """
        return TokenResponse({})

    def post(self, request: HttpRequest) -> HttpResponse:
        """Generate tokens for clients"""
        try:
            with Hub.current.start_span(
                op="authentik.providers.oauth2.post.parse",
            ):
                client_id, client_secret = extract_client_auth(request)
                self.provider = OAuth2Provider.objects.filter(client_id=client_id).first()
                if not self.provider:
                    LOGGER.warning("OAuth2Provider does not exist", client_id=client_id)
                    raise TokenError("invalid_client")
                self.params = TokenParams.parse(request, self.provider, client_id, client_secret)

            with Hub.current.start_span(
                op="authentik.providers.oauth2.post.response",
            ):
                if self.params.grant_type == GRANT_TYPE_AUTHORIZATION_CODE:
                    LOGGER.debug("Converting authorization code to refresh token")
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
        """
        See https://datatracker.ietf.org/doc/html/rfc6749#section-4.1

        Generate a response dictionary containing access token, refresh token, token type, expires in, and ID token.

        Returns:
            dict[str, Any]: The response dictionary.
        """
        now = timezone.now()
        access_token_expiry = now + timedelta_from_string(self.provider.access_token_validity)
        access_token = AccessToken(
            provider=self.provider,
            user=self.params.authorization_code.user,
            expires=access_token_expiry,
            # Keep same scopes as previous token
            scope=self.params.authorization_code.scope,
            auth_time=self.params.authorization_code.auth_time,
        )
        access_token.id_token = IDToken.new(
            self.provider,
            access_token,
            self.request,
        )
        access_token.save()

        refresh_token_expiry = now + timedelta_from_string(self.provider.refresh_token_validity)
        refresh_token = RefreshToken(
            user=self.params.authorization_code.user,
            scope=self.params.authorization_code.scope,
            expires=refresh_token_expiry,
            provider=self.provider,
            auth_time=self.params.authorization_code.auth_time,
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

        # Delete old code
        self.params.authorization_code.delete()
        return {
            "access_token": access_token.token,
            "refresh_token": refresh_token.token,
            "token_type": TOKEN_TYPE,
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": id_token.to_jwt(self.provider),
        }

    def create_refresh_response(self) -> dict[str, Any]:
        """See https://datatracker.ietf.org/doc/html/rfc6749#section-6"""
        unauthorized_scopes = set(self.params.scope) - set(self.params.refresh_token.scope)
        if unauthorized_scopes:
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
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": id_token.to_jwt(self.provider),
        }

    def create_client_credentials_response(self) -> dict[str, Any]:
        """See https://datatracker.ietf.org/doc/html/rfc6749#section-4.4"
        Create a client credentials response.

        This function creates a dictionary containing the client credentials response information. It
        creates an access token based on the current time and the validity duration specified by the
        'provider'. The function also generates an ID token and saves the access token and ID token in
        the database.

        Returns:
            dict[str, Any]: A dictionary containing the client credentials response information.
        """
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
        auth_event = get_login_event(self.request)
        access_token = AccessToken(
            provider=self.provider,
            user=self.params.device_code.user,
            expires=access_token_expiry,
            scope=self.params.device_code.scope,
            auth_time=auth_event.created if auth_event else now,
        )
        access_token.id_token = IDToken.new(
            self.provider,
            access_token,
            self.request,
        )
        access_token.save()

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

        # Delete device code
        self.params.device_code.delete()
        return {
            "access_token": access_token.token,
            "refresh_token": refresh_token.token,
            "token_type": TOKEN_TYPE,
            "expires_in": int(
                timedelta_from_string(self.provider.access_token_validity).total_seconds()
            ),
            "id_token": id_token.to_jwt(self.provider),
        }
