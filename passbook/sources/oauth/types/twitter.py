"""Twitter OAuth Views"""
from typing import Any, Dict

from passbook.sources.oauth.models import OAuthSource, UserOAuthSourceConnection

# from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.views.core import OAuthCallback


# @MANAGER.source(kind=RequestKind.callback, name="Twitter")
class TwitterOAuthCallback(OAuthCallback):
    """Twitter OAuth2 Callback"""

    def get_user_enroll_context(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "username": info.get("screen_name"),
            "email": info.get("email"),
            "name": info.get("name"),
        }
