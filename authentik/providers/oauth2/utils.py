"""OAuth2/OpenID Utils"""
import re
from base64 import b64decode
from binascii import Error
from typing import Any, Optional
from urllib.parse import urlparse

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.http.response import HttpResponseRedirect
from django.utils.cache import patch_vary_headers
from structlog.stdlib import get_logger

from authentik.core.middleware import CTX_AUTH_VIA, KEY_USER
from authentik.events.models import Event, EventAction
from authentik.providers.oauth2.errors import BearerTokenError
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider

LOGGER = get_logger()


class TokenResponse(JsonResponse):
    """JSON Response with headers that it should never be cached

    https://openid.net/specs/openid-connect-core-1_0.html#TokenResponse"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["Cache-Control"] = "no-store"
        self["Pragma"] = "no-cache"


def cors_allow(request: HttpRequest, response: HttpResponse, *allowed_origins: str):
    """Add headers to permit CORS requests from allowed_origins, with or without credentials,
    with any headers."""
    origin = request.META.get("HTTP_ORIGIN")
    if not origin:
        return response

    # OPTIONS requests don't have an authorization header -> hence
    # we can't extract the provider this request is for
    # so for options requests we allow the calling origin without checking
    allowed = request.method == "OPTIONS"
    received_origin = urlparse(origin)
    for allowed_origin in allowed_origins:
        url = urlparse(allowed_origin)
        if (
            received_origin.scheme == url.scheme
            and received_origin.hostname == url.hostname
            and received_origin.port == url.port
        ):
            allowed = True
    if not allowed:
        LOGGER.warning(
            "CORS: Origin is not an allowed origin",
            requested=received_origin,
            allowed=allowed_origins,
        )
        return response

    # From the CORS spec: The string "*" cannot be used for a resource that supports credentials.
    response["Access-Control-Allow-Origin"] = origin
    patch_vary_headers(response, ["Origin"])
    response["Access-Control-Allow-Credentials"] = "true"

    if request.method == "OPTIONS":
        if "HTTP_ACCESS_CONTROL_REQUEST_HEADERS" in request.META:
            response["Access-Control-Allow-Headers"] = request.META[
                "HTTP_ACCESS_CONTROL_REQUEST_HEADERS"
            ]
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    return response


def extract_access_token(request: HttpRequest) -> Optional[str]:
    """
    Get the access token using Authorization Request Header Field method.
    Or try getting via GET.
    See: http://tools.ietf.org/html/rfc6750#section-2.1

    Return a string.
    """
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")

    if re.compile(r"^[Bb]earer\s{1}.+$").match(auth_header):
        return auth_header.split()[1]
    if "access_token" in request.POST:
        return request.POST.get("access_token")
    if "access_token" in request.GET:
        return request.GET.get("access_token")
    return None


def extract_client_auth(request: HttpRequest) -> tuple[str, str]:
    """
    Get client credentials using HTTP Basic Authentication method.
    Or try getting parameters via POST.
    See: http://tools.ietf.org/html/rfc6750#section-2.1

    Return a tuple `(client_id, client_secret)`.
    """
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")

    if re.compile(r"^Basic\s{1}.+$").match(auth_header):
        b64_user_pass = auth_header.split()[1]
        try:
            user_pass = b64decode(b64_user_pass).decode("utf-8").partition(":")
            client_id, _, client_secret = user_pass
        except (ValueError, Error):
            client_id = client_secret = ""  # nosec
    else:
        client_id = request.POST.get("client_id", "")
        client_secret = request.POST.get("client_secret", "")

    return (client_id, client_secret)


def protected_resource_view(scopes: list[str]):
    """View decorator. The client accesses protected resources by presenting the
    access token to the resource server.

    https://datatracker.ietf.org/doc/html/rfc6749#section-7

    This decorator also injects the token into `kwargs`"""

    def wrapper(view):
        def view_wrapper(request: HttpRequest, *args, **kwargs):
            if request.method == "OPTIONS":
                return view(request, *args, **kwargs)
            try:
                access_token = extract_access_token(request)
                if not access_token:
                    LOGGER.debug("No token passed")
                    raise BearerTokenError("invalid_token")

                token = AccessToken.objects.filter(token=access_token).first()
                if not token:
                    LOGGER.debug("Token does not exist", access_token=access_token)
                    raise BearerTokenError("invalid_token")

                if token.is_expired:
                    LOGGER.debug("Token has expired", access_token=access_token)
                    raise BearerTokenError("invalid_token")

                if token.revoked:
                    LOGGER.warning("Revoked token was used", access_token=access_token)
                    Event.new(
                        action=EventAction.SUSPICIOUS_REQUEST,
                        message="Revoked access token was used",
                        token=token,
                        provider=token.provider,
                    ).from_http(request, user=token.user)
                    raise BearerTokenError("invalid_token")

                if not set(scopes).issubset(set(token.scope)):
                    LOGGER.warning(
                        "Scope mismatch.",
                        required=set(scopes),
                        token_has=set(token.scope),
                    )
                    raise BearerTokenError("insufficient_scope")
            except BearerTokenError as error:
                response = HttpResponse(status=error.status)
                response[
                    "WWW-Authenticate"
                ] = f'error="{error.code}", error_description="{error.description}"'
                return response
            kwargs["token"] = token
            CTX_AUTH_VIA.set("oauth_token")
            response = view(request, *args, **kwargs)
            setattr(response, "ak_context", {})
            response.ak_context[KEY_USER] = token.user.username
            return response

        return view_wrapper

    return wrapper


def authenticate_provider(request: HttpRequest) -> Optional[OAuth2Provider]:
    """Attempt to authenticate via Basic auth of client_id:client_secret"""
    client_id, client_secret = extract_client_auth(request)
    if client_id == client_secret == "":
        return None
    provider: Optional[OAuth2Provider] = OAuth2Provider.objects.filter(client_id=client_id).first()
    if not provider:
        return None
    if client_id != provider.client_id or client_secret != provider.client_secret:
        LOGGER.debug("(basic) Provider for basic auth does not exist")
        return None
    return provider


class HttpResponseRedirectScheme(HttpResponseRedirect):
    """HTTP Response to redirect, can be to a non-http scheme"""

    def __init__(
        self,
        redirect_to: str,
        *args: Any,
        allowed_schemes: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> None:
        self.allowed_schemes = allowed_schemes or ["http", "https", "ftp"]
        super().__init__(redirect_to, *args, **kwargs)
