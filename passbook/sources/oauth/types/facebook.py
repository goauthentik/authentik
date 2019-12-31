"""Facebook OAuth Views"""

from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.utils import user_get_or_create
from passbook.sources.oauth.views.core import OAuthCallback, OAuthRedirect


@MANAGER.source(kind=RequestKind.redirect, name="Facebook")
class FacebookOAuthRedirect(OAuthRedirect):
    """Facebook OAuth2 Redirect"""

    def get_additional_parameters(self, source):
        return {
            "scope": "email",
        }


@MANAGER.source(kind=RequestKind.callback, name="Facebook")
class FacebookOAuth2Callback(OAuthCallback):
    """Facebook OAuth2 Callback"""

    def get_or_create_user(self, source, access, info):
        user_data = {
            "username": info.get("name"),
            "email": info.get("email", ""),
            "name": info.get("name"),
            "password": None,
        }
        fb_user = user_get_or_create(**user_data)
        return fb_user
