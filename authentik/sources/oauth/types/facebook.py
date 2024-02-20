"""Facebook OAuth Views"""

from typing import Any, Optional

from facebook import GraphAPI

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class FacebookOAuthRedirect(OAuthRedirect):
    """Facebook OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["email"],
        }


class FacebookOAuth2Client(OAuth2Client):
    """Facebook OAuth2 Client"""

    def get_profile_info(self, token: dict[str, str]) -> Optional[dict[str, Any]]:
        api = GraphAPI(access_token=token["access_token"])
        return api.get_object("me", fields="id,name,email")


class FacebookOAuth2Callback(OAuthCallback):
    """Facebook OAuth2 Callback"""

    client_class = FacebookOAuth2Client

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("name"),
            "email": info.get("email"),
            "name": info.get("name"),
        }


@registry.register()
class FacebookType(SourceType):
    """Facebook Type definition"""

    callback_view = FacebookOAuth2Callback
    redirect_view = FacebookOAuthRedirect
    verbose_name = "Facebook"
    name = "facebook"

    authorization_url = "https://www.facebook.com/v7.0/dialog/oauth"
    access_token_url = "https://graph.facebook.com/v7.0/oauth/access_token"  # nosec
    profile_url = "https://graph.facebook.com/v7.0/me?fields=id,name,email"
