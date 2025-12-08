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
        scopes = ["users.read", "tweet.read"]
        # If admin has defined custom scopes in the provider UI, merge them
        configured = getattr(source, "scope", []) or []
        for s in configured:
            if s not in scopes:
                scopes.append(s)
        return {
            "scope": scopes,
        }



class TwitterOAuthCallback(OAuthCallback):
    """Twitter OAuth2 Callback"""

    client_class = UserprofileHeaderAuthClient

    def get_user_id(self, info: dict[str, str]) -> str:
        return info.get("data", {}).get("id", "")


@registry.register()
class TwitterType(SourceType):
    """Twitter Type definition"""

    callback_view = TwitterOAuthCallback
    redirect_view = TwitterOAuthRedirect
    verbose_name = "Twitter"
    name = "twitter"

    authorization_url = "https://twitter.com/i/oauth2/authorize"
    access_token_url = "https://api.twitter.com/2/oauth2/token"  # nosec
    profile_url = "https://api.twitter.com/2/users/me?user.fields=verified,username,name,profile_image_url,confirmed_email"

    pkce = PKCEMethod.S256

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        data = info.get("data", {})
        email = (
            data.get("confirmed_email")
            or data.get("email")
            or None
        )
        return {
            "username": data.get("username"),
            "email": email,
            "name": data.get("name"),
        }

