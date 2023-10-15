"""Channels base classes"""
from channels.exceptions import DenyConnection
from rest_framework.exceptions import AuthenticationFailed
from structlog.stdlib import get_logger

from authentik.api.authentication import bearer_auth
from authentik.core.models import User

LOGGER = get_logger()


class TokenOutpostConsumer:
    """Authorize a client with a token"""

    user: User

    def connect(self):
        headers = dict(self.scope["headers"])
        if b"authorization" not in headers:
            LOGGER.warning("WS Request without authorization header")
            raise DenyConnection()

        raw_header = headers[b"authorization"]

        try:
            user = bearer_auth(raw_header)
            # user is only None when no header was given, in which case we deny too
            if not user:
                raise DenyConnection()
        except AuthenticationFailed as exc:
            LOGGER.warning("Failed to authenticate", exc=exc)
            raise DenyConnection()

        self.user = user
