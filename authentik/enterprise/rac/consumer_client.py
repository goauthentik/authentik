"""RAC Client consumer"""
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.exceptions import ChannelFull, DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from django.http.request import QueryDict
from guardian.shortcuts import get_objects_for_user

from authentik.core.models import Application
from authentik.enterprise.rac.models import RACProvider
from authentik.outposts.models import Outpost, OutpostState, OutpostType

RAC_CLIENT_GROUP = "group_enterprise_rac_client"

# Step 1: Client connects to this websocket endpoint
# Step 2: We prepare all the connection args for Guac
# Step 3: Send a websocket message to a single outpost that has this provider assigned
#         (Currently sending to all of them)
#         (Should probably do different load balancing algorithms)
# Step 4: Outpost creates a websocket connection back to authentik
#         with /ws/outpost_rac/<our_channel_id>/
# Step 5: This consumer transfers data between the two channels


class RACClientConsumer(AsyncWebsocketConsumer):
    """RAC client consumer the browser connects to"""

    dest_channel_id: str = ""
    provider: RACProvider

    async def connect(self):
        await self.accept("guacamole")
        await self.channel_layer.group_add(RAC_CLIENT_GROUP, self.channel_name)
        await self.init_outpost_connection()

    @database_sync_to_async
    def init_outpost_connection(self):
        """Initialize guac connection settings"""
        app_slug = self.scope["url_route"]["kwargs"]["app"]
        app = get_objects_for_user(
            self.scope["user"], "view_application", Application.objects.filter(slug=app_slug)
        ).first()
        if not app:
            raise DenyConnection()
        self.provider = RACProvider.objects.filter(application=app).first()
        if not self.provider:
            raise DenyConnection()
        params = self.provider.get_settings()
        msg = {
            "type": "event.provider.specific",
            "sub_type": "init_connection",
            "dest_channel_id": self.channel_name,
            "params": params,
            "protocol": self.provider.protocol,
        }
        query = QueryDict(self.scope["query_string"].decode())
        for key in ["screen_width", "screen_height", "screen_dpi", "audio"]:
            value = query.get(key, None)
            if not value:
                continue
            msg[key] = str(value)
        # TODO: Pick random outpost
        for outpost in Outpost.objects.filter(
            type=OutpostType.RAC,
            providers__in=[self.provider],
        ):
            # TODO: Only send to a single outpost
            for state in OutpostState.for_outpost(outpost):
                for channel in state.channel_ids:
                    async_to_sync(self.channel_layer.send)(
                        channel,
                        msg,
                    )

    async def receive(self, text_data=None, bytes_data=None):
        """Mirror data received from client to the dest_channel_id
        which is the channel talking to guacd"""
        if self.dest_channel_id == "":
            return
        # print(f"client - receive - {text_data[:50]}")
        try:
            await self.channel_layer.send(
                self.dest_channel_id,
                {
                    "type": "event.send",
                    "text_data": text_data,
                    "bytes_data": bytes_data,
                },
            )
        except ChannelFull:
            pass

    async def event_outpost_connected(self, event: dict):
        """Handle event broadcasted from outpost consumer, and check if they
        created a connection for us"""
        if event.get("client_channel") != self.channel_name:
            return
        self.dest_channel_id = event.get("outpost_channel")

    async def event_send(self, event: dict):
        """Handler called by outpost websocket that sends data to this specific
        client connection"""
        # print(f"client - send - {event['text_data'][:50]}")
        await self.send(text_data=event.get("text_data"), bytes_data=event.get("bytes_data"))
