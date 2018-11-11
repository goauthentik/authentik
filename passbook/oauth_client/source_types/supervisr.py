"""Supervisr OAuth2 Views"""

import json
from logging import getLogger

from django.contrib.auth import get_user_model
from requests.exceptions import RequestException

from passbook.oauth_client.clients import OAuth2Client
from passbook.oauth_client.utils import user_get_or_create
from passbook.oauth_client.views.core import OAuthCallback
from passbook.oauth_client.source_types.manager import MANAGER, RequestKind

LOGGER = getLogger(__name__)


class SupervisrOAuth2Client(OAuth2Client):
    """Supervisr OAuth2 Client"""

    def get_profile_info(self, raw_token):
        "Fetch user profile information."
        try:
            token = json.loads(raw_token)['access_token']
            headers = {
                'Authorization': 'Bearer:%s' % token
            }
            response = self.request('get', self.source.profile_url,
                                    token=raw_token, headers=headers)
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning('Unable to fetch user profile: %s', exc)
            return None
        else:
            return response.json() or response.text


@MANAGER.source(kind=RequestKind.callback, name='supervisr')
class SupervisrOAuthCallback(OAuthCallback):
    """Supervisr OAuth2 Callback"""

    client_class = SupervisrOAuth2Client

    def get_user_id(self, source, info):
        return info['pk']

    def get_or_create_user(self, source, access, info):
        user = get_user_model()
        user_data = {
            user.USERNAME_FIELD: info.get('username'),
            'email': info.get('email', ''),
            'first_name': info.get('first_name'),
            'password': None,
        }
        sv_user = user_get_or_create(user_model=user, **user_data)
        return sv_user
