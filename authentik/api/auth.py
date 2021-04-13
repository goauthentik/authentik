"""API Authentication"""
from base64 import b64decode, b64encode
from binascii import Error
from typing import Any, Optional, Union

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.core.models import Token, TokenIntents, User

LOGGER = get_logger()


def token_from_header(raw_header: bytes) -> Optional[Token]:
    """raw_header in the Format of `Basic dGVzdDp0ZXN0`"""
    auth_credentials = raw_header.decode()
    if auth_credentials == "":
        return None
    # Legacy, accept basic auth thats fully encoded (2021.3 outposts)
    if " " not in auth_credentials:
        try:
            plain = b64decode(auth_credentials.encode()).decode()
            auth_type, body = plain.split()
            auth_credentials = f"{auth_type} {b64encode(body.encode()).decode()}"
        except (UnicodeDecodeError, Error):
            return None
    auth_type, auth_credentials = auth_credentials.split()
    if auth_type.lower() not in ["basic", "bearer"]:
        LOGGER.debug("Unsupported authentication type, denying", type=auth_type.lower())
        return None
    password = auth_credentials
    if auth_type.lower() == "basic":
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
    """Token-based authentication using HTTP Bearer authentication"""

    def authenticate(self, request: Request) -> Union[tuple[User, Any], None]:
        """Token-based authentication using HTTP Bearer authentication"""
        auth = get_authorization_header(request)

        token = token_from_header(auth)
        if not token:
            return None

        return (token.user, None)

    def authenticate_header(self, request: Request) -> str:
        return "Bearer"
