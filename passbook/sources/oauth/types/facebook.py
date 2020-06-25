"""Facebook OAuth Views"""
from typing import Any, Dict, Optional

from facebook import GraphAPI

from passbook.sources.oauth.clients import OAuth2Client
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


class FacebookOAuth2Client(OAuth2Client):
    """Facebook OAuth2 Client"""

    def get_profile_info(self, token: Dict[str, str]) -> Optional[Dict[str, Any]]:
        api = GraphAPI(access_token=token["access_token"])
        return api.get_object("me", fields="id,name,email")


@MANAGER.source(kind=RequestKind.callback, name="Facebook")
class FacebookOAuth2Callback(OAuthCallback):
    """Facebook OAuth2 Callback"""

    client_class = FacebookOAuth2Client

    def get_or_create_user(self, source, access, info):
        user_data = {
            "username": info.get("name"),
            "email": info.get("email", ""),
            "name": info.get("name"),
            "password": None,
        }
        fb_user = user_get_or_create(**user_data)
        return fb_user
