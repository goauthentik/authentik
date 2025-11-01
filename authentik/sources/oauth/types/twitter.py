"""Twitter OAuth Views"""

from typing import Any

from authentik.sources.oauth.clients.oauth2 import (
    UserprofileHeaderAuthClient,
)
from authentik.sources.oauth.models import PKCEMethod
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class TwitterOAuthRedirect(OAuthRedirect):
    """Twitter OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["users.read", "tweet.read"],
        }


class TwitterOAuthCallback(OAuthCallback):
    """Twitter OAuth2 Callback"""

    client_class = UserprofileHeaderAuthClient


@registry.register()
class TwitterType(SourceType):
    """Twitter Type definition"""

    callback_view = TwitterOAuthCallback
    redirect_view = TwitterOAuthRedirect
    verbose_name = "Twitter"
    name = "twitter"

    authorization_url = "https://twitter.com/i/oauth2/authorize"
    access_token_url = "https://api.twitter.com/2/oauth2/token"  # nosec
    profile_url = "https://api.twitter.com/2/users/me"
    pkce = PKCEMethod.S256

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        data = info.get("data", {})
        return {
            "id": info.get("data", {}).get("id"),
            "username": data.get("username"),
            "email": None,
            "name": data.get("name"),
        }
