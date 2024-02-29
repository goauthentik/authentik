"""Channels base classes"""

from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from rest_framework.exceptions import AuthenticationFailed
from structlog.stdlib import get_logger

from authentik.api.authentication import bearer_auth

LOGGER = get_logger()


class TokenOutpostMiddleware:
    """Authorize a client with a token"""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        await self.auth(scope)
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def auth(self, scope):
        """Authenticate request from header"""
        headers = dict(scope["headers"])
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
            raise DenyConnection() from None

        scope["user"] = user
