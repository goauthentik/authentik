from __future__ import absolute_import, print_function

from requests.exceptions import RequestException

from sentry import http
from sentry.utils import json

from .constants import BASE_DOMAIN


class SupervisrApiError(Exception):
    def __init__(self, message='', status=0):
        super(SupervisrApiError, self).__init__(message)
        self.status = status


class SupervisrClient(object):
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.http = http.build_session()

    def _request(self, path, access_token):
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        headers = {
            'Authorization': 'Bearer {0}'.format(access_token),
        }

        try:
            req = self.http.get('https://{0}/{1}'.format(BASE_DOMAIN, path.lstrip('/')),
                params=params,
                headers=headers,
            )
        except RequestException as e:
            raise SupervisrApiError(unicode(e), status=getattr(e, 'status_code', 0))
        if req.status_code < 200 or req.status_code >= 300:
            raise SupervisrApiError(req.content, status=req.status_code)
        return json.loads(req.content)

    def get_user(self, access_token):
        return self._request('/api/core/v1/accounts/me/?format=openid', access_token)
