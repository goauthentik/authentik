"""Facebook OAuth Views"""
from passbook.channels.in_oauth.types.manager import MANAGER, RequestKind
from passbook.channels.in_oauth.utils import user_get_or_create
from passbook.channels.in_oauth.views.core import OAuthCallback, OAuthRedirect


@MANAGER.inlet(kind=RequestKind.redirect, name="Facebook")
class FacebookOAuthRedirect(OAuthRedirect):
    """Facebook OAuth2 Redirect"""

    def get_additional_parameters(self, inlet):
        return {
            "scope": "email",
        }


@MANAGER.inlet(kind=RequestKind.callback, name="Facebook")
class FacebookOAuth2Callback(OAuthCallback):
    """Facebook OAuth2 Callback"""

    def get_or_create_user(self, inlet, access, info):
        user_data = {
            "username": info.get("name"),
            "email": info.get("email", ""),
            "name": info.get("name"),
            "password": None,
        }
        fb_user = user_get_or_create(**user_data)
        return fb_user
