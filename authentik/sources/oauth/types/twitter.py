"""Twitter OAuth Views"""
from typing import Any

from authentik.sources.oauth.types.manager import MANAGER, SourceType
from authentik.sources.oauth.views.callback import OAuthCallback


class TwitterOAuthCallback(OAuthCallback):
    """Twitter OAuth2 Callback"""

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("screen_name"),
            "email": info.get("email", None),
            "name": info.get("name"),
        }


@MANAGER.type()
class TwitterType(SourceType):
    """Twitter Type definition"""

    callback_view = TwitterOAuthCallback
    name = "Twitter"
    slug = "twitter"

    request_token_url = "https://api.twitter.com/oauth/request_token"  # nosec
    authorization_url = "https://api.twitter.com/oauth/authenticate"
    access_token_url = "https://api.twitter.com/oauth/access_token"  # nosec
    profile_url = "https://api.twitter.com/1.1/account/verify_credentials.json?include_email=true"
