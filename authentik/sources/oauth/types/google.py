"""Google OAuth Views"""
from typing import Any, Dict

from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.types.manager import MANAGER, RequestKind
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


@MANAGER.source(kind=RequestKind.redirect, name="Google")
class GoogleOAuthRedirect(OAuthRedirect):
    """Google OAuth2 Redirect"""

    def get_additional_parameters(self, source):
        return {
            "scope": "email profile",
        }


@MANAGER.source(kind=RequestKind.callback, name="Google")
class GoogleOAuth2Callback(OAuthCallback):
    """Google OAuth2 Callback"""

    def get_user_enroll_context(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "username": info.get("email"),
            "email": info.get("email"),
            "name": info.get("name"),
        }
