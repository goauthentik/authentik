"""AzureAD OAuth2 Views"""
import uuid

from passbook.channels.in_oauth.types.manager import MANAGER, RequestKind
from passbook.channels.in_oauth.utils import user_get_or_create
from passbook.channels.in_oauth.views.core import OAuthCallback


@MANAGER.inlet(kind=RequestKind.callback, name="Azure AD")
class AzureADOAuthCallback(OAuthCallback):
    """AzureAD OAuth2 Callback"""

    def get_user_id(self, inlet, info):
        return uuid.UUID(info.get("objectId")).int

    def get_or_create_user(self, inlet, access, info):
        user_data = {
            "username": info.get("displayName"),
            "email": info.get("mail", None) or info.get("otherMails")[0],
            "name": info.get("displayName"),
            "password": None,
        }
        return user_get_or_create(**user_data)
