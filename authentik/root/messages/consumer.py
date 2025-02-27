"""websocket Message consumer"""

from channels.exceptions import DenyConnection
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.cache import cache

from authentik.root.messages.storage import CACHE_PREFIX


class MessageConsumer(JsonWebsocketConsumer):
    """Consumer which sends django.contrib.messages Messages over WS.
    channel_name is saved into cache with user_id, and when a add_message is called"""

    session_key: str

    def connect(self):
        if not self.scope["user"].is_authenticated():
            raise DenyConnection()
        self.accept()
        self.session_key = self.scope["session"].session_key
        if not self.session_key:
            return
        cache.set(f"{CACHE_PREFIX}{self.session_key}_messages_{self.channel_name}", True, None)

    def disconnect(self, code):
        cache.delete(f"{CACHE_PREFIX}{self.session_key}_messages_{self.channel_name}")

    def event_update(self, event: dict):
        """Event handler which is called by Messages Storage backend"""
        self.send_json(event)
