"""Discord OAuth Views"""

from typing import Any

from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class DiscordOAuthRedirect(OAuthRedirect):
    """Discord OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["email", "identify"],
            "prompt": "none",
        }


class DiscordOAuth2Callback(OAuthCallback):
    """Discord OAuth2 Callback"""


@registry.register()
class DiscordType(SourceType):
    """Discord Type definition"""

    callback_view = DiscordOAuth2Callback
    redirect_view = DiscordOAuthRedirect
    verbose_name = "Discord"
    name = "discord"

    authorization_url = "https://discord.com/api/oauth2/authorize"
    access_token_url = "https://discord.com/api/oauth2/token"  # nosec
    profile_url = "https://discord.com/api/users/@me"

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("username"),
            "email": info.get("email", None),
            "name": info.get("username"),
        }
