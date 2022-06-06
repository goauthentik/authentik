"""SCIM Token auth"""
from base64 import b64decode
from typing import Any, Optional, Union

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request

from authentik.core.models import Token, TokenIntents, User


class SCIMTokenAuth(BaseAuthentication):
    """SCIM Token auth"""

    def legacy(self, key: str, source_slug: str) -> Optional[Token]:
        """Legacy HTTP-Basic auth for testing"""
        _username, _, password = b64decode(key.encode()).decode().partition(":")
        token = self.check_token(password, source_slug)
        if token:
            return (token.user, token)
        return None

    def check_token(self, key: str, source_slug: str) -> Optional[Token]:
        """Check that a token exists, is not expired, and is assigned to the correct source"""
        token = Token.filter_not_expired(key=key, intent=TokenIntents.INTENT_API).first()
        if not token:
            return None
        if not token.scimsource_set.exists():
            return None
        if token.scimsource_set.first().slug != source_slug:
            return None
        return token

    def authenticate(self, request: Request) -> Union[tuple[User, Any], None]:
        kwargs = request._request.resolver_match.kwargs
        source_slug = kwargs.get("source_slug", None)
        auth = get_authorization_header(request).decode()
        auth_type, _, key = auth.partition(" ")
        if auth_type != "Bearer":
            return self.legacy(key, source_slug)
        token = self.check_token(key, source_slug)
        if not token:
            return None
        return (token.user, token)
