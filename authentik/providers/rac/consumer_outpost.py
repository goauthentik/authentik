"""RAC consumer"""

import json

from channels.exceptions import ChannelFull
from channels.generic.websocket import AsyncWebsocketConsumer

from authentik.providers.rac.consumer_client import build_rac_client_group

BULK_CONTROL_MAX_LENGTH = 8 * 1024


class RACOutpostConsumer(AsyncWebsocketConsumer):
    """Consumer the outpost connects to, to send specific data back to a client connection"""

    dest_channel_id: str

    async def connect(self):
        self.dest_channel_id = self.scope["url_route"]["kwargs"]["channel"]
        await self.accept()
        await self.channel_layer.group_send(
            build_rac_client_group(),
            {
                "type": "event.outpost.connected",
                "outpost_channel": self.channel_name,
                "client_channel": self.dest_channel_id,
                "outpost_user": str(self.scope["user"].pk),
            },
        )

    async def receive(self, text_data=None, bytes_data=None):
        """Mirror data received from guacd running in the outpost
        to the dest_channel_id which is the channel talking to the browser"""
        try:
            if text_data and text_data.startswith("0.authentik.bulk."):
                if len(text_data) > BULK_CONTROL_MAX_LENGTH:
                    return
                try:
                    payload = json.loads(text_data.removeprefix("0.authentik.bulk."))
                except ValueError:
                    return
                if isinstance(payload, dict):
                    await self.channel_layer.send(
                        self.dest_channel_id,
                        {
                            "type": "event.file.bulk.reply",
                            "payload": payload,
                            "outpost_channel": self.channel_name,
                        },
                    )
                return
            if text_data and text_data.startswith("0.authentik.list."):
                if len(text_data) > 128 * 1024:
                    return
                try:
                    payload = json.loads(text_data.removeprefix("0.authentik.list."))
                except ValueError:
                    return
                if isinstance(payload, dict):
                    await self.channel_layer.send(
                        self.dest_channel_id,
                        {
                            "type": "event.file.list.reply",
                            "payload": payload,
                            "outpost_channel": self.channel_name,
                        },
                    )
                return
            await self.channel_layer.send(
                self.dest_channel_id,
                {
                    "type": "event.send",
                    "text_data": text_data,
                    "bytes_data": bytes_data,
                    "outpost_channel": self.channel_name,
                },
            )
        except ChannelFull:
            # A lost control reply leaves the browser waiting indefinitely.
            await self.close(code=1013)

    async def disconnect(self, code):
        await self.channel_layer.send(
            self.dest_channel_id,
            {
                "type": "event.disconnect",
                "reason": "outpost_disconnect",
                "outpost_channel": self.channel_name,
            },
        )

    async def event_send(self, event: dict):
        """Handler called by client websocket that sends data to this specific
        outpost connection"""
        await self.send(text_data=event.get("text_data"), bytes_data=event.get("bytes_data"))

    async def event_file_list(self, event: dict):
        await self.send(text_data="0.authentik.list." + event["payload"])

    async def event_file_bulk(self, event: dict):
        await self.send(text_data="0.authentik.bulk." + event["payload"])

    async def event_disconnect(self, event: dict):
        """Tell outpost we're about to disconnect"""
        await self.send(text_data="0.authentik.disconnect")
        await self.close()
