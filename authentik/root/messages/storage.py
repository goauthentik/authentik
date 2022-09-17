"""Channels Messages storage"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.messages.storage.base import BaseStorage, Message
from django.core.cache import cache
from django.http.request import HttpRequest


class ChannelsStorage(BaseStorage):
    """Send contrib.messages over websocket"""

    def __init__(self, request: HttpRequest) -> None:
        # pyright: reportGeneralTypeIssues=false
        super().__init__(request)
        self.channel = get_channel_layer()

    def _get(self):
        return [], True

    def _store(self, messages: list[Message], response, *args, **kwargs):
        prefix = f"user_{self.request.session.session_key}_messages_"
        keys = cache.keys(f"{prefix}*")
        for key in keys:
            uid = key.replace(prefix, "")
            for message in messages:
                async_to_sync(self.channel.send)(
                    uid,
                    {
                        "type": "event.update",
                        "message_type": "message",
                        "level": message.level_tag,
                        "tags": message.tags,
                        "message": message.message,
                    },
                )
