"""Reddit OAuth Views"""
import json
from logging import getLogger

from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from passbook.oauth_client.clients import OAuth2Client
from passbook.oauth_client.source_types.manager import MANAGER, RequestKind
from passbook.oauth_client.utils import user_get_or_create
from passbook.oauth_client.views.core import OAuthCallback, OAuthRedirect

LOGGER = getLogger(__name__)


@MANAGER.source(kind=RequestKind.redirect, name='reddit')
class RedditOAuthRedirect(OAuthRedirect):
    """Reddit OAuth2 Redirect"""

    def get_additional_parameters(self, source):
        return {
            'scope': 'identity',
            'duration': 'permanent',
        }


class RedditOAuth2Client(OAuth2Client):
    """Reddit OAuth2 Client"""

    def get_access_token(self, request, callback=None, **request_kwargs):
        "Fetch access token from callback request."
        auth = HTTPBasicAuth(
            self.source.consumer_key,
            self.source.consumer_secret)
        return super(RedditOAuth2Client, self).get_access_token(request, callback, auth=auth)

    def get_profile_info(self, raw_token):
        "Fetch user profile information."
        try:
            token = json.loads(raw_token)
            headers = {
                'Authorization': '%s %s' % (token['token_type'], token['access_token'])
            }
            response = self.request('get', self.source.profile_url,
                                    token=token['access_token'], headers=headers)
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning('Unable to fetch user profile: %s', exc)
            return None
        else:
            return response.json() or response.text


@MANAGER.source(kind=RequestKind.callback, name='reddit')
class RedditOAuth2Callback(OAuthCallback):
    """Reddit OAuth2 Callback"""

    client_class = RedditOAuth2Client

    def get_or_create_user(self, source, access, info):
        user_data = {
            'username': info.get('name'),
            'email': None,
            'first_name': info.get('name'),
            'password': None,
        }
        reddit_user = user_get_or_create(**user_data)
        return reddit_user
