"""Reddit OAuth Views"""
from requests.auth import HTTPBasicAuth

from passbook.channels.in_oauth.clients import OAuth2Client
from passbook.channels.in_oauth.types.manager import MANAGER, RequestKind
from passbook.channels.in_oauth.utils import user_get_or_create
from passbook.channels.in_oauth.views.core import OAuthCallback, OAuthRedirect


@MANAGER.inlet(kind=RequestKind.redirect, name="reddit")
class RedditOAuthRedirect(OAuthRedirect):
    """Reddit OAuth2 Redirect"""

    def get_additional_parameters(self, inlet):
        return {
            "scope": "identity",
            "duration": "permanent",
        }


class RedditOAuth2Client(OAuth2Client):
    """Reddit OAuth2 Client"""

    def get_access_token(self, request, callback=None, **request_kwargs):
        "Fetch access token from callback request."
        auth = HTTPBasicAuth(self.inlet.consumer_key, self.inlet.consumer_secret)
        return super(RedditOAuth2Client, self).get_access_token(
            request, callback, auth=auth
        )


@MANAGER.inlet(kind=RequestKind.callback, name="reddit")
class RedditOAuth2Callback(OAuthCallback):
    """Reddit OAuth2 Callback"""

    client_class = RedditOAuth2Client

    def get_or_create_user(self, inlet, access, info):
        user_data = {
            "username": info.get("name"),
            "email": None,
            "name": info.get("name"),
            "password": None,
        }
        reddit_user = user_get_or_create(**user_data)
        return reddit_user
