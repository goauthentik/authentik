"""Channels base classes"""
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.exceptions import ValidationError
from structlog import get_logger

from passbook.core.models import Token, TokenIntents, User

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

        token = headers[b"authorization"]
        try:
            token_uuid = token.decode("utf-8")
            tokens = Token.filter_not_expired(
                token_uuid=token_uuid, intent=TokenIntents.INTENT_API
            )
            if not tokens.exists():
                LOGGER.warning("WS Request with invalid token")
                self.close()
                return False
        except ValidationError:
            LOGGER.warning("WS Invalid UUID")
            self.close()
            return False
        self.user = tokens.first().user
        return True
