"""websocket Message consumer"""
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.cache import cache


class MessageConsumer(JsonWebsocketConsumer):
    """Consumer which sends django.contrib.messages Messages over WS.
    channel_name is saved into cache with user_id, and when a add_message is called"""

    def connect(self):
        self.accept()
        cache.set(f"user_{self.scope['user'].pk}_{self.channel_name}", True)

    # pylint: disable=unused-argument
    def disconnect(self, close_code):
        cache.delete(f"user_{self.scope['user'].pk}_{self.channel_name}")

    def event_update(self, event: dict):
        """Event handler which is called by Messages Storage backend"""
        self.send_json(event)
