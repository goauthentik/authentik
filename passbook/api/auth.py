"""API Authentication"""
from base64 import b64decode
from typing import Any, Optional, Tuple, Union

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request
from structlog import get_logger

from passbook.core.models import Token, TokenIntents, User

LOGGER = get_logger()


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
    except UnicodeDecodeError:
        # TODO: Remove this workaround
        # temporary fallback for 0.11 to 0.12 upgrade
        # 0.11 and below proxy sends authorization header not base64 encoded
        pass
    # Accept credentials with username and without
    if ":" in auth_credentials:
        _, password = auth_credentials.split(":")
    else:
        password = auth_credentials
    if password == "":
        return None
    tokens = Token.filter_not_expired(key=password, intent=TokenIntents.INTENT_API)
    if not tokens.exists():
        LOGGER.debug("Token not found")
        return None
    return tokens.first()


class PassbookTokenAuthentication(BaseAuthentication):
    """Token-based authentication using HTTP Basic authentication"""

    def authenticate(self, request: Request) -> Union[Tuple[User, Any], None]:
        """Token-based authentication using HTTP Basic authentication"""
        auth = get_authorization_header(request)

        token = token_from_header(auth)
        if not token:
            return None

        return (token.user, None)

    def authenticate_header(self, request: Request) -> str:
        return 'Basic realm="passbook"'
