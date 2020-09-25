"""Reddit OAuth Views"""
from typing import Any, Dict

from requests.auth import HTTPBasicAuth

from passbook.sources.oauth.clients.oauth2 import OAuth2Client
from passbook.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.views.callback import OAuthCallback
from passbook.sources.oauth.views.redirect import OAuthRedirect


@MANAGER.source(kind=RequestKind.redirect, name="reddit")
class RedditOAuthRedirect(OAuthRedirect):
    """Reddit OAuth2 Redirect"""

    def get_additional_parameters(self, source):
        return {
            "scope": "identity",
            "duration": "permanent",
        }


class RedditOAuth2Client(OAuth2Client):
    """Reddit OAuth2 Client"""

    def get_access_token(self, request, callback=None, **request_kwargs):
        "Fetch access token from callback request."
        auth = HTTPBasicAuth(self.source.consumer_key, self.source.consumer_secret)
        return super(RedditOAuth2Client, self).get_access_token(
            request, callback, auth=auth
        )


@MANAGER.source(kind=RequestKind.callback, name="reddit")
class RedditOAuth2Callback(OAuthCallback):
    """Reddit OAuth2 Callback"""

    client_class = RedditOAuth2Client

    def get_user_enroll_context(
        self,
        source: OAuthSource,
        access: UserOAuthSourceConnection,
        info: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "username": info.get("name"),
            "email": None,
            "name": info.get("name"),
            "password": None,
        }
