"""Channels base classes"""
from channels.generic.websocket import JsonWebsocketConsumer
from structlog import get_logger

from passbook.api.auth import token_from_header
from passbook.core.models import User

LOGGER = get_logger()


class AuthJsonConsumer(JsonWebsocketConsumer):
    """Authorize a client with a token"""

    user: User

    def connect(self):
        headers = dict(self.scope["headers"])
        if b"authorization" not in headers:
            LOGGER.warning("WS Request without authorization header")
            self.close()
            return False

        raw_header = headers[b"authorization"]

        token = token_from_header(raw_header)
        if not token:
            LOGGER.warning("Failed to authenticate")
            self.close()
            return False

        self.user = token.user
        return True
