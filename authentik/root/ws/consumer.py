"""websocket Message consumer"""

from hashlib import sha256

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.cache import cache
from django.db import connection

from authentik.root.ws.storage import CACHE_PREFIX


def build_session_group(session_key: str):
    return sha256(
        f"{connection.schema_name}/group_client_session_{str(session_key)}".encode()
    ).hexdigest()


def build_device_group(session_key: str):
    return sha256(
        f"{connection.schema_name}/group_client_device_{str(session_key)}".encode()
    ).hexdigest()


class MessageConsumer(JsonWebsocketConsumer):
    """Consumer which sends django.contrib.messages Messages over WS.
    channel_name is saved into cache with user_id, and when a add_message is called"""

    session_key: str
    device_cookie: str | None = None

    def connect(self):
        self.accept()
        self.session_key = self.scope["session"].session_key
        if self.session_key:
            cache.set(f"{CACHE_PREFIX}{self.session_key}_messages_{self.channel_name}", True, None)
        if device_cookie := self.scope["cookies"]["authentik_device"]:
            self.device_cookie = device_cookie
            async_to_sync(self.channel_layer.group_add)(
                build_device_group(self.device_cookie), self.channel_name
            )

    def disconnect(self, code):
        if self.session_key:
            cache.delete(f"{CACHE_PREFIX}{self.session_key}_messages_{self.channel_name}")
        if self.device_cookie:
            print("removing from group", build_session_group(self.session_key))
            async_to_sync(self.channel_layer.group_discard)(
                build_device_group(self.device_cookie), self.channel_name
            )

    def event_message(self, event: dict):
        """Event handler which is called by Messages Storage backend"""
        self.send_json(event)

    def event_session_authenticated(self, event: dict):
        """Event handler post user authentication"""
        self.send_json({"message_type": "session.authenticated"})
