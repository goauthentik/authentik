"""SSF Token auth"""

from typing import TYPE_CHECKING, Any

from django.db.models import Q
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request

from authentik.core.models import Token, TokenIntents, User
from authentik.enterprise.providers.ssf.models import SSFProvider
from authentik.providers.oauth2.models import AccessToken

if TYPE_CHECKING:
    from authentik.enterprise.providers.ssf.views.base import SSFView


class SSFTokenAuth(BaseAuthentication):
    """SSF Token auth"""

    view: "SSFView"

    def __init__(self, view: "SSFView") -> None:
        super().__init__()
        self.view = view

    def check_token(self, key: str) -> Token | None:
        """Check that a token exists, is not expired, and is assigned to the correct provider"""
        token = Token.filter_not_expired(key=key, intent=TokenIntents.INTENT_API).first()
        if not token:
            return None
        provider: SSFProvider = token.ssfprovider_set.first()
        if not provider:
            return None
        self.view.application = provider.backchannel_application
        self.view.provider = provider
        return token

    def check_jwt(self, jwt: str) -> AccessToken | None:
        """Check JWT-based authentication, this supports tokens issued either by providers
        configured directly in the provider, and by providers assigned to the application
        that the SSF provider is a backchannel provider of."""
        token = AccessToken.filter_not_expired(token=jwt, revoked=False).first()
        if not token:
            return None
        ssf_provider = SSFProvider.objects.filter(
            Q(oidc_auth_providers__in=[token.provider])
            | Q(backchannel_application__provider__in=[token.provider]),
        ).first()
        if not ssf_provider:
            return None
        self.view.application = ssf_provider.backchannel_application
        self.view.provider = ssf_provider
        return token

    def authenticate(self, request: Request) -> tuple[User, Any] | None:
        auth = get_authorization_header(request).decode()
        auth_type, _, key = auth.partition(" ")
        if auth_type != "Bearer":
            return None
        token = self.check_token(key)
        if token:
            return (token.user, token)
        jwt_token = self.check_jwt(key)
        if jwt_token:
            return (jwt_token.user, token)
        return None
