"""GitHub OAuth Views"""
from passbook.channels.in_oauth.types.manager import MANAGER, RequestKind
from passbook.channels.in_oauth.utils import user_get_or_create
from passbook.channels.in_oauth.views.core import OAuthCallback


@MANAGER.inlet(kind=RequestKind.callback, name="GitHub")
class GitHubOAuth2Callback(OAuthCallback):
    """GitHub OAuth2 Callback"""

    def get_or_create_user(self, inlet, access, info):
        user_data = {
            "username": info.get("login"),
            "email": info.get("email", ""),
            "name": info.get("name"),
            "password": None,
        }
        gh_user = user_get_or_create(**user_data)
        return gh_user
