"""Discord OAuth Views"""
from passbook.channels.in_oauth.types.manager import MANAGER, RequestKind
from passbook.channels.in_oauth.utils import user_get_or_create
from passbook.channels.in_oauth.views.core import OAuthCallback, OAuthRedirect


@MANAGER.inlet(kind=RequestKind.redirect, name="Discord")
class DiscordOAuthRedirect(OAuthRedirect):
    """Discord OAuth2 Redirect"""

    def get_additional_parameters(self, inlet):
        return {
            "scope": "email identify",
        }


@MANAGER.inlet(kind=RequestKind.callback, name="Discord")
class DiscordOAuth2Callback(OAuthCallback):
    """Discord OAuth2 Callback"""

    def get_or_create_user(self, inlet, access, info):
        user_data = {
            "username": info.get("username"),
            "email": info.get("email", "None"),
            "name": info.get("username"),
            "password": None,
        }
        discord_user = user_get_or_create(**user_data)
        return discord_user
