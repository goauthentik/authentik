"""OpenID Connect OAuth Views"""
from typing import Dict

from passbook.sources.oauth.models import OAuthSource
from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.utils import user_get_or_create
from passbook.sources.oauth.views.core import OAuthCallback, OAuthRedirect


@MANAGER.source(kind=RequestKind.redirect, name="OpenID Connect")
class OpenIDConnectOAuthRedirect(OAuthRedirect):
    """OpenIDConnect OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):
        return {
            "scope": "openid email",
        }


@MANAGER.source(kind=RequestKind.callback, name="OpenID Connect")
class OpenIDConnectOAuth2Callback(OAuthCallback):
    """OpenIDConnect OAuth2 Callback"""

    def get_user_id(self, source: OAuthSource, info: Dict[str, str]):
        return info.get("sub")

    def get_or_create_user(self, source: OAuthSource, access, info: Dict[str, str]):
        user_data = {
            "username": info.get("username"),
            "email": info.get("email"),
            "name": info.get("username"),
            "password": None,
        }
        return user_get_or_create(**user_data)
