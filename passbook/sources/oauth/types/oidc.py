"""OpenID Connect OAuth Views"""
from typing import Any, Dict

from passbook.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.views.core import OAuthCallback, OAuthRedirect


@MANAGER.source(kind=RequestKind.redirect, name="OpenID Connect")
class OpenIDConnectOAuthRedirect(OAuthRedirect):
    """OpenIDConnect OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):
        return {
            "scope": "openid email profile",
        }


@MANAGER.source(kind=RequestKind.callback, name="OpenID Connect")
class OpenIDConnectOAuth2Callback(OAuthCallback):
    """OpenIDConnect OAuth2 Callback"""

    def get_user_id(self, source: OAuthSource, info: Dict[str, str]) -> str:
        return info.get("sub", "")

    def get_user_enroll_context(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "username": info.get("nickname"),
            "email": info.get("email"),
            "name": info.get("name"),
        }
