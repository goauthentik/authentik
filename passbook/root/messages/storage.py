"""Channels Messages storage"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.messages.storage.base import Message
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.http.request import HttpRequest


class ChannelsStorage(FallbackStorage):
    """Send contrib.messages over websocket"""

    def __init__(self, request: HttpRequest) -> None:
        # pyright: reportGeneralTypeIssues=false
        super().__init__(request)
        self.channel = get_channel_layer()

    def _store(self, messages: list[Message], response, *args, **kwargs):
        prefix = f"user_{self.request.user.pk}_messages_"
        keys = cache.keys(f"{prefix}*")
        for key in keys:
            uid = key.replace(prefix, "")
            for message in messages:
                async_to_sync(self.channel.send)(
                    uid,
                    {
                        "type": "event.update",
                        "levelTag": message.level_tag,
                        "tags": message.tags,
                        "message": message.message,
                    },
                )
        return super()._store(messages, response, *args, **kwargs)
