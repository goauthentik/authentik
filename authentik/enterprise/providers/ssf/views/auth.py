"""SSF Token auth"""

from base64 import b64decode
from typing import Any

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request
from rest_framework.views import APIView

from authentik.core.models import Token, TokenIntents, User
from authentik.enterprise.providers.ssf.models import SSFProvider


class SSFTokenAuth(BaseAuthentication):
    """SCIM Token auth"""

    def __init__(self, view: APIView) -> None:
        super().__init__()
        self.view = view

    def legacy(self, key: str, source_slug: str) -> Token | None:  # pragma: no cover
        """Legacy HTTP-Basic auth for testing"""
        if not settings.TEST and not settings.DEBUG:
            return None
        _username, _, password = b64decode(key.encode()).decode().partition(":")
        token = self.check_token(password, source_slug)
        if token:
            return (token.user, token)
        return None

    def check_token(self, key: str, source_slug: str) -> Token | None:
        """Check that a token exists, is not expired, and is assigned to the correct source"""
        token = Token.filter_not_expired(key=key, intent=TokenIntents.INTENT_API).first()
        if not token:
            return None
        provider: SSFProvider = token.ssfprovider_set.first()
        if not provider:
            return None
        self.view.application = provider.application
        self.view.provider = provider
        return token

    def authenticate(self, request: Request) -> tuple[User, Any] | None:
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
