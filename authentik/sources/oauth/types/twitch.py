"""Twitch OAuth Views"""

from json import dumps
from typing import Any

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect


class TwitchClient(UserprofileHeaderAuthClient):
    """Twitch needs the token_type to be capitalized for the request header."""

    def get_profile_info(self, token: dict[str, str]) -> dict[str, Any] | None:
        token["token_type"] = token["token_type"].capitalize()
        return super().get_profile_info(token)


class TwitchOAuthRedirect(OAuthRedirect):
    """Twitch OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        claims = {"userinfo": {"email": None, "preferred_username": None}}
        return {
            "scope": ["openid"],
            "claims": dumps(claims),
        }


class TwitchOAuth2Callback(OpenIDConnectOAuth2Callback):
    """Twitch OAuth2 Callback"""

    client_class = TwitchClient


@registry.register()
class TwitchType(SourceType):
    """Twitch Type definition"""

    callback_view = TwitchOAuth2Callback
    redirect_view = TwitchOAuthRedirect
    verbose_name = "Twitch"
    name = "twitch"

    authorization_url = "https://id.twitch.tv/oauth2/authorize"
    access_token_url = "https://id.twitch.tv/oauth2/token"  # nosec
    profile_url = "https://id.twitch.tv/oauth2/userinfo"

    authorization_code_auth_method = AuthorizationCodeAuthMethod.POST_BODY

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("preferred_username"),
            "email": info.get("email"),
            "name": info.get("preferred_username"),
        }
