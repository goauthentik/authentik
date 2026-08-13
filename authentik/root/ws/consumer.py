"""websocket Message consumer"""

from hashlib import sha256

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.db import connection

from authentik.core.models import User


def build_user_group(user: User):
    return sha256(f"{connection.schema_name}/group_client_user_{user.uuid}".encode()).hexdigest()


class MessageConsumer(JsonWebsocketConsumer):
    """Consumer which sends django.contrib.messages Messages over WS.
    channel_name is saved into cache with user_id, and when a add_message is called"""

    session_key: str
    user: User | None = None

    def connect(self):
        self.accept()
        self.session_key = self.scope["session"].session_key
        if user := self.scope.get("user"):
            if user.is_authenticated:
                async_to_sync(self.channel_layer.group_add)(
                    build_user_group(user), self.channel_name
                )

    def disconnect(self, code):
        if self.user:
            async_to_sync(self.channel_layer.group_discard)(
                build_user_group(self.user), self.channel_name
            )

    def event_notification(self, event: dict):
        """Event handler for new notifications"""
        self.send_json({"message_type": "notification.new", **event})
