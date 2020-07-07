"""Twitter OAuth Views"""
# from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.utils import user_get_or_create
from passbook.sources.oauth.views.core import OAuthCallback


# @MANAGER.source(kind=RequestKind.callback, name="Twitter")
class TwitterOAuthCallback(OAuthCallback):
    """Twitter OAuth2 Callback"""

    def get_or_create_user(self, source, access, info):
        user_data = {
            "username": info.get("screen_name"),
            "email": info.get("email", ""),
            "name": info.get("name"),
            "password": None,
        }
        tw_user = user_get_or_create(**user_data)
        return tw_user
