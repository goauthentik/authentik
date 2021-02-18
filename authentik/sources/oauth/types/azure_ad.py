"""AzureAD OAuth2 Views"""
from typing import Any
from uuid import UUID

from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.types.manager import MANAGER, RequestKind
from authentik.sources.oauth.views.callback import OAuthCallback


@MANAGER.source(kind=RequestKind.callback, name="Azure AD")
class AzureADOAuthCallback(OAuthCallback):
    """AzureAD OAuth2 Callback"""

    def get_user_id(self, source: OAuthSource, info: dict[str, Any]) -> str:
        return str(UUID(info.get("objectId")).int)

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
