"""API Authentication"""

from typing import Any

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import SCOPE_AUTHENTIK_API
from authentik.core.middleware import CTX_AUTH_VIA
from authentik.core.models import Token, TokenIntents, User

LOGGER = get_logger()


def validate_auth(header: bytes) -> str | None:
    """Validate that the header is in a correct format,
    returns type and credentials"""
    auth_credentials = header.decode().strip()
    if auth_credentials == "" or " " not in auth_credentials:
        return None
    auth_type, _, auth_credentials = auth_credentials.partition(" ")
    if auth_type.lower() != "bearer":
        LOGGER.debug("Unsupported authentication type, denying", type=auth_type.lower())
        raise AuthenticationFailed("Unsupported authentication type")
    if auth_credentials == "":  # nosec # noqa
        raise AuthenticationFailed("Malformed header")
    return auth_credentials


def bearer_auth(raw_header: bytes) -> User | None:
    """raw_header in the Format of `Bearer ....`"""
    user = auth_user_lookup(raw_header)
    if not user:
        return None
    if not user.is_active:
        raise AuthenticationFailed("Token invalid/expired")
    return user


def auth_user_lookup(raw_header: bytes) -> User | None:
    """raw_header in the Format of `Bearer ....`"""
    from authentik.providers.oauth2.models import AccessToken

    auth_credentials = validate_auth(raw_header)
    if not auth_credentials:
        return None
    # first, check traditional tokens
    key_token = Token.filter_not_expired(
        key=auth_credentials, intent=TokenIntents.INTENT_API
    ).first()
    if key_token:
        CTX_AUTH_VIA.set("api_token")
        return key_token.user
    # then try to auth via JWT
    jwt_token = AccessToken.filter_not_expired(
        token=auth_credentials, _scope__icontains=SCOPE_AUTHENTIK_API
    ).first()
    if jwt_token:
        # Double-check scopes, since they are saved in a single string
        # we want to check the parsed version too
        if SCOPE_AUTHENTIK_API not in jwt_token.scope:
            raise AuthenticationFailed("Token invalid/expired")
        CTX_AUTH_VIA.set("jwt")
        return jwt_token.user
    raise AuthenticationFailed("Token invalid/expired")


class TokenAuthentication(BaseAuthentication):
    """Token-based authentication using HTTP Bearer authentication"""

    def authenticate(self, request: Request) -> tuple[User, Any] | None:
        """Token-based authentication using HTTP Bearer authentication"""
        auth = get_authorization_header(request)

        user = bearer_auth(auth)
        # None is only returned when the header isn't set.
        if not user:
            return None

        return (user, None)  # pragma: no cover


class TokenSchema(OpenApiAuthenticationExtension):
    """Auth schema"""

    target_class = TokenAuthentication
    name = "authentik"

    def get_security_definition(self, auto_schema):
        """Auth schema"""
        return {"type": "http", "scheme": "bearer"}
