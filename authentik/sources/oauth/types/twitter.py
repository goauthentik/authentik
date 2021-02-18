"""Twitter OAuth Views"""
from typing import Any

from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.types.manager import MANAGER, RequestKind
from authentik.sources.oauth.views.callback import OAuthCallback


@MANAGER.source(kind=RequestKind.callback, name="Twitter")
class TwitterOAuthCallback(OAuthCallback):
    """Twitter OAuth2 Callback"""

    def get_user_enroll_context(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("screen_name"),
            "email": info.get("email", None),
            "name": info.get("name"),
        }
