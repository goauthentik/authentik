"""AzureAD OAuth2 Views"""
import uuid
from typing import Any, Dict

from passbook.core.models import User
from passbook.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.utils import user_get_or_create
from passbook.sources.oauth.views.core import OAuthCallback


@MANAGER.source(kind=RequestKind.callback, name="Azure AD")
class AzureADOAuthCallback(OAuthCallback):
    """AzureAD OAuth2 Callback"""

    def get_user_id(self, source: OAuthSource, info: Dict[str, Any]) -> str:
        return str(uuid.UUID(info.get("objectId")).int)

    def get_or_create_user(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> User:
        user_data = {
            "username": info.get("displayName"),
            "email": info.get("mail", None) or info.get("otherMails")[0],
            "name": info.get("displayName"),
            "password": None,
        }
        return user_get_or_create(**user_data)
