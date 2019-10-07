"""Twitter OAuth Views"""

from requests.exceptions import RequestException
from structlog import get_logger

from passbook.sources.oauth.clients import OAuthClient
from passbook.sources.oauth.types.manager import MANAGER, RequestKind
from passbook.sources.oauth.utils import user_get_or_create
from passbook.sources.oauth.views.core import OAuthCallback

LOGGER = get_logger()


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
        user_data = {
            'username': info.get('screen_name'),
            'email': info.get('email', ''),
            'name': info.get('name'),
            'password': None,
        }
        tw_user = user_get_or_create(**user_data)
        return tw_user
