"""passbook oauth_client Authorization backend"""

from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from passbook.sources.oauth.models import (OAuthSource,
                                           UserOAuthSourceConnection)


class AuthorizedServiceBackend(ModelBackend):
    "Authentication backend for users registered with remote OAuth provider."

    def authenticate(self, request, source=None, identifier=None):
        "Fetch user for a given source by id."
        source_q = Q(source__name=source)
        if isinstance(source, OAuthSource):
            source_q = Q(source=source)
        try:
            access = UserOAuthSourceConnection.objects.filter(
                source_q, identifier=identifier
            ).select_related('user')[0]
        except IndexError:
            return None
        else:
            return access.user
