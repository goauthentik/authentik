"""AzureAD OAuth2 Views"""
import uuid
from typing import Any, Dict

from passbook.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.views.core import OAuthCallback


@MANAGER.source(kind=RequestKind.callback, name="Azure AD")
class AzureADOAuthCallback(OAuthCallback):
    """AzureAD OAuth2 Callback"""

    def get_user_id(self, source: OAuthSource, info: Dict[str, Any]) -> str:
        return str(uuid.UUID(info.get("objectId")).int)

    def get_user_enroll_context(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> Dict[str, Any]:
        mail = info.get("mail", None) or info.get("otherMails", [None])[0]
        return {
            "username": info.get("displayName"),
            "email": mail,
            "name": info.get("displayName"),
        }
