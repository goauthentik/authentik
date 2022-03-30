"""API Authentication"""
from typing import Any, Optional

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.core.middleware import KEY_AUTH_VIA, LOCAL
from authentik.core.models import Token, TokenIntents, User
from authentik.outposts.models import Outpost

LOGGER = get_logger()


def validate_auth(header: bytes) -> str:
    """Validate that the header is in a correct format,
    returns type and credentials"""
    auth_credentials = header.decode().strip()
    if auth_credentials == "" or " " not in auth_credentials:
        return None
    auth_type, _, auth_credentials = auth_credentials.partition(" ")
    if auth_type.lower() != "bearer":
        LOGGER.debug("Unsupported authentication type, denying", type=auth_type.lower())
        raise AuthenticationFailed("Unsupported authentication type")
    if auth_credentials == "":  # nosec
        raise AuthenticationFailed("Malformed header")
    return auth_credentials


def bearer_auth(raw_header: bytes) -> Optional[User]:
    """raw_header in the Format of `Bearer ....`"""
    auth_credentials = validate_auth(raw_header)
    if not auth_credentials:
        return None
    # first, check traditional tokens
    token = Token.filter_not_expired(key=auth_credentials, intent=TokenIntents.INTENT_API).first()
    if hasattr(LOCAL, "authentik"):
        LOCAL.authentik[KEY_AUTH_VIA] = "api_token"
    if token:
        return token.user
    user = token_secret_key(auth_credentials)
    if user:
        return user
    raise AuthenticationFailed("Token invalid/expired")


def token_secret_key(value: str) -> Optional[User]:
    """Check if the token is the secret key
    and return the service account for the managed outpost"""
    from authentik.outposts.managed import MANAGED_OUTPOST

    if value != settings.SECRET_KEY:
        return None
    outposts = Outpost.objects.filter(managed=MANAGED_OUTPOST)
    if not outposts:
        return None
    if hasattr(LOCAL, "authentik"):
        LOCAL.authentik[KEY_AUTH_VIA] = "secret_key"
    outpost = outposts.first()
    return outpost.user


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
