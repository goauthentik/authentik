"""Google OAuth Views"""
from passbook.channels.in_oauth.types.manager import MANAGER, RequestKind
from passbook.channels.in_oauth.utils import user_get_or_create
from passbook.channels.in_oauth.views.core import OAuthCallback, OAuthRedirect


@MANAGER.inlet(kind=RequestKind.redirect, name="Google")
class GoogleOAuthRedirect(OAuthRedirect):
    """Google OAuth2 Redirect"""

    def get_additional_parameters(self, inlet):
        return {
            "scope": "email profile",
        }


@MANAGER.inlet(kind=RequestKind.callback, name="Google")
class GoogleOAuth2Callback(OAuthCallback):
    """Google OAuth2 Callback"""

    def get_or_create_user(self, inlet, access, info):
        user_data = {
            "username": info.get("email"),
            "email": info.get("email", ""),
            "name": info.get("name"),
            "password": None,
        }
        google_user = user_get_or_create(**user_data)
        return google_user
