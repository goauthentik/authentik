"""Classlink OAuth Views"""

from typing import Any

from requests.auth import HTTPBasicAuth

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class ClasslinkOAuthRedirect(OAuthRedirect):
    """Classlink OAuth2 Redirect"""


class ClasslinkOAuth2Client(UserprofileHeaderAuthClient):
    """Classlink OAuth2 Client"""

    def check_application_state(self) -> bool:
        """Always return True"""
        return True

class ClasslinkOAuth2Callback(OAuthCallback):
    """Classlink OAuth2 Callback"""

    client_class = ClasslinkOAuth2Client

    def get_user_id(self, info: dict[str, str]) -> str:
            return info.get("sub", None)

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("nickname", info.get("preferred_username")),
            "email": info.get("email"),
            "name": info.get("name"),
        }


@registry.register()
class ClasslinkType(SourceType):
    """Classlink Type definition"""

    callback_view = ClasslinkOAuth2Callback
    redirect_view = ClasslinkOAuthRedirect

    verbose_name = "Classlink"
    name = "classlink"

    authorization_url = "https://launchpad.classlink.com/oauth2/v2/auth"
    access_token_url = "https://launchpad.classlink.com/oauth2/v2/token"
    profile_url = "https://nodeapi.classlink.com/v2/my/profileinfo"
