"""Channels Messages storage"""
from asgiref.sync import async_to_sync
from channels import DEFAULT_CHANNEL_LAYER
from channels.layers import channel_layers
from django.contrib.messages.storage.base import Message
from django.contrib.messages.storage.session import SessionStorage
from django.core.cache import cache
from django.http.request import HttpRequest

SESSION_KEY = "_messages"
CACHE_PREFIX = "goauthentik.io/root/messages_"


async def closing_send(channel, message):
    """Wrapper around layer send that closes the connection"""
    # See https://github.com/django/channels_redis/issues/332
    # TODO: Remove this after channels_redis 4.1 is released
    channel_layer = channel_layers.make_backend(DEFAULT_CHANNEL_LAYER)
    await channel_layer.send(channel, message)
    await channel_layer.close_pools()


class ChannelsStorage(SessionStorage):
    """Send contrib.messages over websocket"""

    def __init__(self, request: HttpRequest) -> None:
        # pyright: reportGeneralTypeIssues=false
        super().__init__(request)

    def _store(self, messages: list[Message], response, *args, **kwargs):
        prefix = f"{CACHE_PREFIX}{self.request.session.session_key}_messages_"
        keys = cache.keys(f"{prefix}*")
        # if no active connections are open, fallback to storing messages in the
        # session, so they can always be retrieved
        if len(keys) < 1:
            return super()._store(messages, response, *args, **kwargs)
        for key in keys:
            uid = key.replace(prefix, "")
            for message in messages:
                async_to_sync(closing_send)(
                    uid,
                    {
                        "type": "event.update",
                        "message_type": "message",
                        "level": message.level_tag,
                        "tags": message.tags,
                        "message": message.message,
                    },
                )
        return []
