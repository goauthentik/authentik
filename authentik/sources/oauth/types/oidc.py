"""OpenID Connect OAuth Views"""
from typing import Any

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class OpenIDConnectOAuthRedirect(OAuthRedirect):
    """OpenIDConnect OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": ["openid", "email", "profile"],
        }


class OpenIDConnectOAuth2Callback(OAuthCallback):
    """OpenIDConnect OAuth2 Callback"""

    client_class = UserprofileHeaderAuthClient

    def get_user_id(self, info: dict[str, str]) -> str:
        return info.get("sub", "")

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("nickname", info.get("preferred_username")),
            "email": info.get("email"),
            "name": info.get("name"),
        }


@registry.register()
class OpenIDConnectType(SourceType):
    """OpenIDConnect Type definition"""

    callback_view = OpenIDConnectOAuth2Callback
    redirect_view = OpenIDConnectOAuthRedirect
    name = "OpenID Connect"
    slug = "openidconnect"

    urls_customizable = True
