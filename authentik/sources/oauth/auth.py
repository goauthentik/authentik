"""authentik oauth_client Authorization backend"""
from typing import Optional

from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

from authentik.core.models import User
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection


class AuthorizedServiceBackend(ModelBackend):
    "Authentication backend for users registered with remote OAuth provider."

    def authenticate(
        self, request: HttpRequest, source: OAuthSource, identifier: str
    ) -> Optional[User]:
        "Fetch user for a given source by id."
        access = UserOAuthSourceConnection.objects.filter(
            source=source, identifier=identifier
        ).select_related("user")
        if not access.exists():
            return None
        return access.first().user
