"""Google OAuth Views"""
from passbook.oauth_client.source_types.manager import MANAGER, RequestKind
from passbook.oauth_client.utils import user_get_or_create
from passbook.oauth_client.views.core import OAuthCallback, OAuthRedirect


@MANAGER.source(kind=RequestKind.redirect, name='Google')
class GoogleOAuthRedirect(OAuthRedirect):
    """Google OAuth2 Redirect"""

    def get_additional_parameters(self, source):
        return {
            'scope': 'email profile',
        }


@MANAGER.source(kind=RequestKind.callback, name='Google')
class GoogleOAuth2Callback(OAuthCallback):
    """Google OAuth2 Callback"""

    def get_or_create_user(self, source, access, info):
        user_data = {
            'username': info.get('email'),
            'email': info.get('email', ''),
            'name': info.get('name'),
            'password': None,
        }
        google_user = user_get_or_create(**user_data)
        return google_user
