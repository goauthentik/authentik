"""GitHub OAuth Views"""

from django.contrib.auth import get_user_model

from passbook.oauth_client.source_types.manager import MANAGER, RequestKind
from passbook.oauth_client.utils import user_get_or_create
from passbook.oauth_client.views.core import OAuthCallback


@MANAGER.source(kind=RequestKind.callback, name='GitHub')
class GitHubOAuth2Callback(OAuthCallback):
    """GitHub OAuth2 Callback"""

    def get_or_create_user(self, source, access, info):
        user = get_user_model()
        user_data = {
            user.USERNAME_FIELD: info.get('login'),
            'email': info.get('email', ''),
            'first_name': info.get('name'),
            'password': None,
        }
        gh_user = user_get_or_create(user_model=user, **user_data)
        return gh_user
