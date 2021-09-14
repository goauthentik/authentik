"""AzureAD OAuth2 Views"""
from typing import Any, Optional

from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.types.manager import MANAGER, SourceType
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()


class AzureADOAuthRedirect(OAuthRedirect):
    """Azure AD OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": "openid https://graph.microsoft.com/User.Read",
        }


class AzureADClient(OAuth2Client):
    """Azure AD Oauth client, azure ad doesn't like the ?access_token that is sent by default"""

    def get_profile_info(self, token: dict[str, str]) -> Optional[dict[str, Any]]:
        "Fetch user profile information."
        profile_url = self.source.type.profile_url or ""
        if self.source.type.urls_customizable and self.source.profile_url:
            profile_url = self.source.profile_url
        try:
            response = self.session.request(
                "get",
                profile_url,
                headers={"Authorization": f"{token['token_type']} {token['access_token']}"},
            )
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch user profile", exc=exc)
            return None
        else:
            return response.json()


class AzureADOAuthCallback(OAuthCallback):
    """AzureAD OAuth2 Callback"""

    client_class = AzureADClient

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        mail = info.get("mail", None) or info.get("otherMails", [None])[0]
        return {
            "username": info.get("displayName"),
            "email": mail,
            "name": info.get("displayName"),
        }


@MANAGER.type()
class AzureADType(SourceType):
    """Azure AD Type definition"""

    callback_view = AzureADOAuthCallback
    redirect_view = AzureADOAuthRedirect
    name = "Azure AD"
    slug = "azuread"

    urls_customizable = True

    authorization_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    access_token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"  # nosec
    profile_url = "https://graph.microsoft.com/v1.0/me"
