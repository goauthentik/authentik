"""AzureAD OAuth2 Views"""
import json
import uuid

from requests.exceptions import RequestException
from structlog import get_logger

from passbook.sources.oauth.clients import OAuth2Client
from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.utils import user_get_or_create
from passbook.sources.oauth.views.core import OAuthCallback

LOGGER = get_logger()


class AzureADOAuth2Client(OAuth2Client):
    """AzureAD OAuth2 Client"""

    def get_profile_info(self, raw_token):
        "Fetch user profile information."
        try:
            token = json.loads(raw_token)["access_token"]
            headers = {"Authorization": "Bearer %s" % token}
            response = self.request("get", self.source.profile_url, headers=headers)
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch user profile: %s", exc)
            return None
        else:
            return response.json() or response.text


@MANAGER.source(kind=RequestKind.callback, name="Azure AD")
class AzureADOAuthCallback(OAuthCallback):
    """AzureAD OAuth2 Callback"""

    client_class = AzureADOAuth2Client

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
