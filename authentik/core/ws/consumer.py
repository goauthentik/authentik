"""websocket Message consumer"""
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.cache import cache


class FrontendConsumer(JsonWebsocketConsumer):
    """Consumer which sends django.contrib.messages Messages over WS.
    channel_name is saved into cache with user_id, and when a add_message is called"""

    session_key: str

    def connect(self):
        self.accept()
        self.session_key = self.scope["session"].session_key
        cache.set(f"user_{self.session_key}_messages_{self.channel_name}", True, None)

    # pylint: disable=unused-argument
    def disconnect(self, code):
        cache.delete(f"user_{self.session_key}_messages_{self.channel_name}")

    def event_update(self, event: dict):
        """Event handler which is called by Messages Storage backend"""
        self.send_json(event)

        # prefix = f"user_{self.request.session.session_key}_messages_"
        # keys = cache.keys(f"{prefix}*")
        # for key in keys:
        #     uid = key.replace(prefix, "")
        #     for message in messages:
        #         async_to_sync(self.channel.send)(
        #             uid,
        #             {
        #                 "type": "event.update",
        #                 "message_type": "message",
        #                 "level": message.level_tag,
        #                 "tags": message.tags,
        #                 "message": message.message,
        #             },
        #         )
