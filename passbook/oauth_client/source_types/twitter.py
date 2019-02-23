"""Twitter OAuth Views"""

from logging import getLogger

from django.contrib.auth import get_user_model
from requests.exceptions import RequestException

from passbook.oauth_client.clients import OAuthClient
from passbook.oauth_client.source_types.manager import MANAGER, RequestKind
from passbook.oauth_client.utils import user_get_or_create
from passbook.oauth_client.views.core import OAuthCallback

LOGGER = getLogger(__name__)


class TwitterOAuthClient(OAuthClient):
    """Twitter OAuth2 Client"""

    def get_profile_info(self, raw_token):
        "Fetch user profile information."
        try:
            response = self.request('get', self.source.profile_url + "?include_email=true",
                                    token=raw_token)
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning('Unable to fetch user profile: %s', exc)
            return None
        else:
            return response.json() or response.text


@MANAGER.source(kind=RequestKind.callback, name='Twitter')
class TwitterOAuthCallback(OAuthCallback):
    """Twitter OAuth2 Callback"""

    client_class = TwitterOAuthClient

    def get_or_create_user(self, source, access, info):
        user = get_user_model()
        user_data = {
            user.USERNAME_FIELD: info.get('screen_name'),
            'email': info.get('email', ''),
            'first_name': info.get('name'),
            'password': None,
        }
        tw_user = user_get_or_create(user_model=user, **user_data)
        return tw_user
