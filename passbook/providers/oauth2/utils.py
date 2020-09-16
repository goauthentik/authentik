"""OAuth2/OpenID Utils"""
import re
from base64 import b64decode
from binascii import Error
from typing import List, Tuple

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.cache import patch_vary_headers
from jwkest.jwt import JWT
from structlog import get_logger

from passbook.providers.oauth2.errors import BearerTokenError
from passbook.providers.oauth2.models import RefreshToken

LOGGER = get_logger()


class TokenResponse(JsonResponse):
    """JSON Response with headers that it should never be cached

    https://openid.net/specs/openid-connect-core-1_0.html#TokenResponse"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["Cache-Control"] = "no-store"
        self["Pragma"] = "no-cache"


def cors_allow_any(request, response):
    """
    Add headers to permit CORS requests from any origin, with or without credentials,
    with any headers.
    """
    origin = request.META.get("HTTP_ORIGIN")
    if not origin:
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


def extract_access_token(request: HttpRequest) -> str:
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
    return ""


def extract_client_auth(request: HttpRequest) -> Tuple[str, str]:
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
            user_pass = b64decode(b64_user_pass).decode("utf-8").split(":")
            client_id, client_secret = user_pass
        except (ValueError, Error):
            client_id = client_secret = ""
    else:
        client_id = request.POST.get("client_id", "")
        client_secret = request.POST.get("client_secret", "")

    return (client_id, client_secret)


def protected_resource_view(scopes: List[str]):
    """View decorator. The client accesses protected resources by presenting the
    access token to the resource server.

    https://tools.ietf.org/html/rfc6749#section-7

    This decorator also injects the token into `kwargs`"""

    def wrapper(view):
        def view_wrapper(request, *args, **kwargs):
            access_token = extract_access_token(request)

            try:
                try:
                    kwargs["token"] = RefreshToken.objects.get(
                        access_token=access_token
                    )
                except RefreshToken.DoesNotExist:
                    LOGGER.debug("Token does not exist", access_token=access_token)
                    raise BearerTokenError("invalid_token")

                if kwargs["token"].is_expired:
                    LOGGER.debug("Token has expired", access_token=access_token)
                    raise BearerTokenError("invalid_token")

                if not set(scopes).issubset(set(kwargs["token"].scope)):
                    LOGGER.warning(
                        "Scope missmatch.",
                        required=set(scopes),
                        token_has=set(kwargs["token"].scope),
                    )
                    raise BearerTokenError("insufficient_scope")
            except BearerTokenError as error:
                response = HttpResponse(status=error.status)
                response[
                    "WWW-Authenticate"
                ] = f'error="{error.code}", error_description="{error.description}"'
                return response

            return view(request, *args, **kwargs)

        return view_wrapper

    return wrapper


def client_id_from_id_token(id_token):
    """
    Extracts the client id from a JSON Web Token (JWT).
    Returns a string or None.
    """
    payload = JWT().unpack(id_token).payload()
    aud = payload.get("aud", None)
    if aud is None:
        return None
    if isinstance(aud, list):
        return aud[0]
    return aud
