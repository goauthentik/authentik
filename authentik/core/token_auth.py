"""Authenticate with tokens"""

from typing import Any, Optional

from django.contrib.auth.backends import ModelBackend
from django.http.request import HttpRequest

from authentik.core.models import Token, TokenIntents, User


class TokenBackend(ModelBackend):
    """Authenticate with token"""

    def authenticate(
        self, request: HttpRequest, username: Optional[str], password: Optional[str], **kwargs: Any
    ) -> Optional[User]:
        try:
            user = User._default_manager.get_by_natural_key(username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
            return None
        tokens = Token.filter_not_expired(
            user=user, key=password, intent=TokenIntents.INTENT_APP_PASSWORD
        )
        if not tokens.exists():
            return None
        return tokens.first().user
