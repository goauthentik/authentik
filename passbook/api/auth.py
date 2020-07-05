"""API Authentication"""
from base64 import b64decode
from typing import Any, Tuple, Union

from django.utils.translation import gettext as _
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request

from passbook.core.models import Token, TokenIntents, User


class PassbookTokenAuthentication(BaseAuthentication):
    """Token-based authentication using HTTP Basic authentication"""

    def authenticate(self, request: Request) -> Union[Tuple[User, Any], None]:
        """Token-based authentication using HTTP Basic authentication"""
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b"basic":
            return None

        if len(auth) == 1:
            msg = _("Invalid basic header. No credentials provided.")
            raise exceptions.AuthenticationFailed(msg)
        if len(auth) > 2:
            msg = _(
                "Invalid basic header. Credentials string should not contain spaces."
            )
            raise exceptions.AuthenticationFailed(msg)

        header_data = b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(":")

        tokens = Token.filter_not_expired(
            token_uuid=header_data[2], intent=TokenIntents.INTENT_API
        )
        if not tokens.exists():
            raise exceptions.AuthenticationFailed(_("Invalid token."))

        return (tokens.first().user, None)

    def authenticate_header(self, request: Request) -> str:
        return 'Basic realm="passbook"'
