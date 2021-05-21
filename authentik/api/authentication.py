"""API Authentication"""
from base64 import b64decode
from binascii import Error
from typing import Any, Optional, Union

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.core.models import Token, TokenIntents, User

LOGGER = get_logger()


# pylint: disable=too-many-return-statements
def token_from_header(raw_header: bytes) -> Optional[Token]:
    """raw_header in the Format of `Bearer dGVzdDp0ZXN0`"""
    auth_credentials = raw_header.decode()
    if auth_credentials == "":
        return None
    auth_type, auth_credentials = auth_credentials.split()
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
            _, password = auth_credentials.split(":")
        else:
            password = auth_credentials
    if password == "":  # nosec
        raise AuthenticationFailed("Malformed header")
    tokens = Token.filter_not_expired(key=password, intent=TokenIntents.INTENT_API)
    if not tokens.exists():
        raise AuthenticationFailed("Token invalid/expired")
    return tokens.first()


class TokenAuthentication(BaseAuthentication):
    """Token-based authentication using HTTP Bearer authentication"""

    def authenticate(self, request: Request) -> Union[tuple[User, Any], None]:
        """Token-based authentication using HTTP Bearer authentication"""
        auth = get_authorization_header(request)

        token = token_from_header(auth)
        # None is only returned when the header isn't set.
        if not token:
            return None

        return (token.user, None)  # pragma: no cover
