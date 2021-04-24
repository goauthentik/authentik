"""AzureAD OAuth2 Views"""
from typing import Any, Optional
from uuid import UUID

from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.types.manager import MANAGER, SourceType
from authentik.sources.oauth.views.callback import OAuthCallback


class AzureADOAuthCallback(OAuthCallback):
    """AzureAD OAuth2 Callback"""

    def get_user_id(self, source: OAuthSource, info: dict[str, Any]) -> Optional[str]:
        try:
            return str(UUID(info.get("objectId")).int)
        except TypeError:
            return None

    def get_user_enroll_context(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
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
    name = "Azure AD"
    slug = "azure-ad"

    urls_customizable = True

    authorization_url = "https://login.microsoftonline.com/common/oauth2/authorize"
    access_token_url = "https://login.microsoftonline.com/common/oauth2/token"  # nosec
    profile_url = "https://graph.windows.net/myorganization/me?api-version=1.6"
