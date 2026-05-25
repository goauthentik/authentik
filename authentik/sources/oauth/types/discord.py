"""Discord OAuth Views"""

from typing import Any

from requests import RequestException

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class DiscordOAuthRedirect(OAuthRedirect):
    """Discord OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        scopes = ["email", "identify"]

        if source.discord_guild_id:
            scopes.append("guilds.members.read")

        return {
            "scope": scopes,
            "prompt": "none",
        }


class DiscordOAuth2Client(OAuth2Client):
    """Discord OAuth2 Client"""

    def get_guild_member(self, guild_id: str, token: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.do_request(
                "GET",
                f"https://discord.com/api/v10/users/@me/guilds/{guild_id}/member",
                token=token,
            )
        except RequestException as exc:
            self.logger.warning("Unable to fetch discord guild member", exc=exc)
            return {}
        return response.json()


class DiscordOAuth2Callback(OAuthCallback):
    """Discord OAuth2 Callback"""

    client_class = DiscordOAuth2Client


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

    def get_base_user_properties(
        self,
        info: dict[str, Any],
        client: DiscordOAuth2Client,
        token: dict[str, Any],
        source: OAuthSource,
        **kwargs,
    ) -> dict[str, Any]:
        role_ids = []
        if source.discord_guild_id and "guilds.members.read" in token["scope"]:
            member = client.get_guild_member(source.discord_guild_id, token=token)
            role_ids = member.get("roles", [])

        avatar_url = (
            f"https://cdn.discordapp.com/avatars/{info["id"]}/{info["avatar"]}.png?size=64"
            if info["avatar"] is not None
            else None
        )

        return {
            "username": info.get("username"),
            "email": info.get("email", None),
            "name": info.get("global_name", info.get("username")),
            "groups": role_ids,
            "attributes": {
                "discord_avatar": avatar_url,
            },
        }

    def get_base_group_properties(self, source: OAuthSource, group_id: str, **kwargs):
        return {"name": f"{group_id}@discord"}
