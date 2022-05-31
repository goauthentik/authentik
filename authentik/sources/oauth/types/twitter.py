"""Twitter OAuth Views"""
from typing import Any

from authentik.lib.generators import generate_id
from authentik.sources.oauth.clients.oauth2 import SESSION_KEY_OAUTH_PKCE
from authentik.sources.oauth.types.azure_ad import AzureADClient
from authentik.sources.oauth.types.manager import MANAGER, SourceType
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class TwitterOAuthRedirect(OAuthRedirect):
    """Twitter OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        self.request.session[SESSION_KEY_OAUTH_PKCE] = generate_id()
        return {
            "scope": ["users.read", "tweet.read"],
            "code_challenge": self.request.session[SESSION_KEY_OAUTH_PKCE],
            "code_challenge_method": "plain",
        }


class TwitterOAuthCallback(OAuthCallback):
    """Twitter OAuth2 Callback"""

    # Twitter has the same quirk as azure and throws an error if the access token
    # is set via query parameter, so we re-use the azure client
    # see https://github.com/goauthentik/authentik/issues/1910
    client_class = AzureADClient

    def get_user_id(self, info: dict[str, str]) -> str:
        return info.get("data", {}).get("id", "")

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        data = info.get("data", {})
        return {
            "username": data.get("username"),
            "email": None,
            "name": data.get("name"),
        }


@MANAGER.type()
class TwitterType(SourceType):
    """Twitter Type definition"""

    callback_view = TwitterOAuthCallback
    redirect_view = TwitterOAuthRedirect
    name = "Twitter"
    slug = "twitter"

    authorization_url = "https://twitter.com/i/oauth2/authorize"
    access_token_url = "https://api.twitter.com/2/oauth2/token"  # nosec
    profile_url = "https://api.twitter.com/2/users/me"
