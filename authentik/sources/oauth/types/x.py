"""X OAuth Views"""

from typing import Any

from authentik.lib.generators import generate_id
from authentik.sources.oauth.clients.oauth2 import (
    SESSION_KEY_OAUTH_PKCE,
    UserprofileHeaderAuthClient,
)
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class XOAuthRedirect(OAuthRedirect):
    """X OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        self.request.session[SESSION_KEY_OAUTH_PKCE] = generate_id()
        return {
            "scope": ["users.read", "tweet.read"],
            "code_challenge": self.request.session[SESSION_KEY_OAUTH_PKCE],
            "code_challenge_method": "plain",
        }


class XOAuthCallback(OAuthCallback):
    """X OAuth2 Callback"""

    client_class = UserprofileHeaderAuthClient

    def get_user_id(self, info: dict[str, str]) -> str:
        return info.get("data", {}).get("id", "")


@registry.register()
class XType(SourceType):
    """X Type definition"""

    callback_view = XOAuthCallback
    redirect_view = XOAuthRedirect
    verbose_name = "X"
    name = "x"

    authorization_url = "https://twitter.com/i/oauth2/authorize"
    access_token_url = "https://api.twitter.com/2/oauth2/token"  # nosec
    profile_url = "https://api.twitter.com/2/users/me"

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        data = info.get("data", {})
        return {
            "username": data.get("username"),
            "email": None,
            "name": data.get("name"),
        }
