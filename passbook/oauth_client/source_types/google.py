"""Google OAuth Views"""
from django.contrib.auth import get_user_model

from passbook.oauth_client.utils import user_get_or_create
from passbook.oauth_client.views.core import OAuthCallback, OAuthRedirect
from passbook.oauth_client.source_types.manager import MANAGER, RequestKind


@MANAGER.source(kind=RequestKind.redirect, name='google')
class GoogleOAuthRedirect(OAuthRedirect):
    """Google OAuth2 Redirect"""

    def get_additional_parameters(self, source):
        return {
            'scope': 'email profile',
        }


@MANAGER.source(kind=RequestKind.callback, name='google')
class GoogleOAuth2Callback(OAuthCallback):
    """Google OAuth2 Callback"""

    def get_or_create_user(self, source, access, info):
        user = get_user_model()
        user_data = {
            user.USERNAME_FIELD: info.get('email'),
            'email': info.get('email', ''),
            'first_name': info.get('name'),
            'password': None,
        }
        google_user = user_get_or_create(user_model=user, **user_data)
        return google_user
