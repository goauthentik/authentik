"""API Authentication"""
from base64 import b64decode
from binascii import Error
from typing import Any, Optional, Union

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.core.models import Token, TokenIntents, User

LOGGER = get_logger()
X_AUTHENTIK_PREVENT_BASIC_HEADER = "HTTP_X_AUTHENTIK_PREVENT_BASIC"


def token_from_header(raw_header: bytes) -> Optional[Token]:
    """raw_header in the Format of `Basic dGVzdDp0ZXN0`"""
    auth_credentials = raw_header.decode()
    # Accept headers with Type format and without
    if " " in auth_credentials:
        auth_type, auth_credentials = auth_credentials.split()
        if auth_type.lower() != "basic":
            LOGGER.debug(
                "Unsupported authentication type, denying", type=auth_type.lower()
            )
            return None
    try:
        auth_credentials = b64decode(auth_credentials.encode()).decode()
    except (UnicodeDecodeError, Error):
        return None
    # Accept credentials with username and without
    if ":" in auth_credentials:
        _, password = auth_credentials.split(":")
    else:
        password = auth_credentials
    if password == "":  # nosec
        return None
    tokens = Token.filter_not_expired(key=password, intent=TokenIntents.INTENT_API)
    if not tokens.exists():
        LOGGER.debug("Token not found")
        return None
    return tokens.first()


class AuthentikTokenAuthentication(BaseAuthentication):
    """Token-based authentication using HTTP Basic authentication"""

    def authenticate(self, request: Request) -> Union[tuple[User, Any], None]:
        """Token-based authentication using HTTP Basic authentication"""
        auth = get_authorization_header(request)

        token = token_from_header(auth)
        if not token:
            return None

        return (token.user, None)

    def authenticate_header(self, request: Request) -> str:
        if X_AUTHENTIK_PREVENT_BASIC_HEADER in request._request.META:
            return ""
        return 'Basic realm="authentik"'
