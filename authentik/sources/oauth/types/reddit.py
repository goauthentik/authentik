"""Reddit OAuth Views"""

from typing import Any

from requests.auth import HTTPBasicAuth

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class RedditOAuthRedirect(OAuthRedirect):
    """Reddit OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["identity"],
            "duration": "permanent",
        }


class RedditOAuth2Client(UserprofileHeaderAuthClient):
    """Reddit OAuth2 Client"""

    def get_access_token(self, **request_kwargs):
        "Fetch access token from callback request."
        request_kwargs["auth"] = HTTPBasicAuth(self.source.consumer_key, self.source.consumer_secret)
        return super().get_access_token(**request_kwargs)


class RedditOAuth2Callback(OAuthCallback):
    """Reddit OAuth2 Callback"""

    client_class = RedditOAuth2Client


@registry.register()
class RedditType(SourceType):
    """Reddit Type definition"""

    callback_view = RedditOAuth2Callback
    redirect_view = RedditOAuthRedirect
    verbose_name = "Reddit"
    name = "reddit"

    authorization_url = "https://www.reddit.com/api/v1/authorize"
    access_token_url = "https://www.reddit.com/api/v1/access_token"  # nosec
    profile_url = "https://oauth.reddit.com/api/v1/me"

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("name"),
            "email": None,
            "name": info.get("name"),
        }
