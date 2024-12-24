"""SSF Token auth"""

from typing import Any

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request
from rest_framework.views import APIView

from authentik.core.models import Token, TokenIntents, User
from authentik.enterprise.providers.ssf.models import SSFProvider
from authentik.providers.oauth2.models import AccessToken


class SSFTokenAuth(BaseAuthentication):
    """SCIM Token auth"""

    def __init__(self, view: APIView) -> None:
        super().__init__()
        self.view = view

    def check_token(self, key: str) -> Token | None:
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

    def check_jwt(self, jwt: str, provider_pk: int) -> AccessToken | None:
        token = AccessToken.filter_not_expired(token=jwt, revoked=False).first()
        if not token:
            return None
        ssf_provider = SSFProvider.objects.filter(
            pk=provider_pk, oidc_auth_providers__in=[token.provider]
        ).first()
        if not ssf_provider:
            return None
        self.view.application = ssf_provider.application
        self.view.provider = ssf_provider
        return token

    def authenticate(self, request: Request) -> tuple[User, Any] | None:
        kwargs = request._request.resolver_match.kwargs
        provider = kwargs.get("provider", None)
        auth = get_authorization_header(request).decode()
        auth_type, _, key = auth.partition(" ")
        if auth_type != "Bearer":
            return None
        token = self.check_token(key)
        if token:
            return (token.user, token)
        jwt_token = self.check_jwt(key, provider)
        if jwt_token:
            return (jwt_token.user, token)
        return None
