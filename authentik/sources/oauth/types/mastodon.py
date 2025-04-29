"""OpenID Connect OAuth Views"""
from typing import Any

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class MastodonClient(OAuth2Client):
    """Mastodon OAuth2 Client"""

    def get_access_token(self, **request_kwargs):
        "Fetch access token from callback request."
        auth = HTTPBasicAuth(self.source.consumer_key, self.source.consumer_secret)
        return super().get_access_token(auth=auth)

class MastodonOAuthRedirect(OAuthRedirect):
    """Mastodon OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": ["read"]
        }


class MastodonOAuth2Callback(OAuthCallback):
    """Mastodon OAuth2 Callback"""

    client_class = MastodonClient
    
    def get_user_id(self, info: dict[str, str]) -> str:
        return info.get("username", "")

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("username"),
            "name": info.get("display_name")
        }


@registry.register()
class MastodonType(SourceType):
    """Mastodon Type definition"""

    callback_view = MastodonOAuth2Callback
    redirect_view = MastodonOAuthRedirect
    name = "Mastodon"
    slug = "Mastodon"

    urls_customizable = True
