from __future__ import absolute_import, print_function

from django.conf import settings

CLIENT_ID = getattr(settings, 'PASSBOOK_APP_ID', None)

CLIENT_SECRET = getattr(settings, 'PASSBOOK_API_SECRET', None)

SCOPE = 'openid:userinfo'

BASE_DOMAIN = getattr(settings, 'PASSBOOK_BASE_DOMAIN', 'id.beryju.org')

ACCESS_TOKEN_URL = 'https://{0}/application/oauth/token/'.format(BASE_DOMAIN)
AUTHORIZE_URL = 'https://{0}/application/oauth/authorize/'.format(BASE_DOMAIN)
