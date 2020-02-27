"""AzureAD OAuth2 Views"""
import uuid

from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.utils import user_get_or_create
from passbook.sources.oauth.views.core import OAuthCallback


@MANAGER.source(kind=RequestKind.callback, name="Azure AD")
class AzureADOAuthCallback(OAuthCallback):
    """AzureAD OAuth2 Callback"""

    def get_user_id(self, source, info):
        return uuid.UUID(info.get("objectId")).int

    def get_or_create_user(self, source, access, info):
        user_data = {
            "username": info.get("displayName"),
            "email": info.get("mail", None) or info.get("otherMails")[0],
            "name": info.get("displayName"),
            "password": None,
        }
        return user_get_or_create(**user_data)
