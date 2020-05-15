"""Twitter OAuth Views"""
from passbook.channels.in_oauth.types.manager import MANAGER, RequestKind
from passbook.channels.in_oauth.utils import user_get_or_create
from passbook.channels.in_oauth.views.core import OAuthCallback


@MANAGER.inlet(kind=RequestKind.callback, name="Twitter")
class TwitterOAuthCallback(OAuthCallback):
    """Twitter OAuth2 Callback"""

    def get_or_create_user(self, inlet, access, info):
        user_data = {
            "username": info.get("screen_name"),
            "email": info.get("email", ""),
            "name": info.get("name"),
            "password": None,
        }
        tw_user = user_get_or_create(**user_data)
        return tw_user
