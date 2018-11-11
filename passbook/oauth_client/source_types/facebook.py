"""Facebook OAuth Views"""

from django.contrib.auth import get_user_model

from passbook.oauth_client.errors import OAuthClientEmailMissingError
from passbook.oauth_client.utils import user_get_or_create
from passbook.oauth_client.views.core import OAuthCallback, OAuthRedirect
from passbook.oauth_client.source_types.manager import MANAGER, RequestKind


@MANAGER.source(kind=RequestKind.redirect, name='facebook')
class FacebookOAuthRedirect(OAuthRedirect):
    """Facebook OAuth2 Redirect"""

    def get_additional_parameters(self, source):
        return {
            'scope': 'email',
        }


@MANAGER.source(kind=RequestKind.callback, name='facebook')
class FacebookOAuth2Callback(OAuthCallback):
    """Facebook OAuth2 Callback"""

    def get_or_create_user(self, source, access, info):
        if 'email' not in info:
            raise OAuthClientEmailMissingError()
        user = get_user_model()
        user_data = {
            user.USERNAME_FIELD: info.get('name'),
            'email': info.get('email', ''),
            'first_name': info.get('name'),
            'password': None,
        }
        fb_user = user_get_or_create(user_model=user, **user_data)
        return fb_user
