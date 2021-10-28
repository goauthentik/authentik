"""API Authentication"""
from base64 import b64decode
from binascii import Error
from typing import Any, Optional, Union

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.core.middleware import KEY_AUTH_VIA, LOCAL
from authentik.core.models import Token, TokenIntents, User
from authentik.outposts.models import Outpost

LOGGER = get_logger()


# pylint: disable=too-many-return-statements
def bearer_auth(raw_header: bytes) -> Optional[User]:
    """raw_header in the Format of `Bearer dGVzdDp0ZXN0`"""
    auth_credentials = raw_header.decode()
    if auth_credentials == "" or " " not in auth_credentials:
        return None
    auth_type, _, auth_credentials = auth_credentials.partition(" ")
    if auth_type.lower() not in ["basic", "bearer"]:
        LOGGER.debug("Unsupported authentication type, denying", type=auth_type.lower())
        raise AuthenticationFailed("Unsupported authentication type")
    password = auth_credentials
    if auth_type.lower() == "basic":
        try:
            auth_credentials = b64decode(auth_credentials.encode()).decode()
        except (UnicodeDecodeError, Error):
            raise AuthenticationFailed("Malformed header")
        # Accept credentials with username and without
        if ":" in auth_credentials:
            _, _, password = auth_credentials.partition(":")
        else:
            password = auth_credentials
    if password == "":  # nosec
        raise AuthenticationFailed("Malformed header")
    tokens = Token.filter_not_expired(key=password, intent=TokenIntents.INTENT_API)
    if not tokens.exists():
        user = token_secret_key(password)
        if not user:
            raise AuthenticationFailed("Token invalid/expired")
        return user
    if hasattr(LOCAL, "authentik"):
        LOCAL.authentik[KEY_AUTH_VIA] = "api_token"
    return tokens.first().user


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

    def authenticate(self, request: Request) -> Union[tuple[User, Any], None]:
        """Token-based authentication using HTTP Bearer authentication"""
        auth = get_authorization_header(request)

        user = bearer_auth(auth)
        # None is only returned when the header isn't set.
        if not user:
            return None

        return (user, None)  # pragma: no cover
