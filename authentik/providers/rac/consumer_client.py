"""RAC Client consumer"""

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.exceptions import ChannelFull, DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from django.http.request import QueryDict
from structlog.stdlib import BoundLogger, get_logger

from authentik.outposts.consumer import OUTPOST_GROUP_INSTANCE
from authentik.outposts.models import Outpost, OutpostState, OutpostType
from authentik.providers.rac.models import ConnectionToken, RACProvider

# Global broadcast group, which messages are sent to when the outpost connects back
# to authentik for a specific connection
# The `RACClientConsumer` consumer adds itself to this group on connection,
# and removes itself once it has been assigned a specific outpost channel
RAC_CLIENT_GROUP = "group_rac_client"
# A group for all connections in a given authentik session ID
# A disconnect message is sent to this group when the session expires/is deleted
RAC_CLIENT_GROUP_SESSION = "group_rac_client_%(session)s"
# A group for all connections with a specific token, which in almost all cases
# is just one connection, however this is used to disconnect the connection
# when the token is deleted
RAC_CLIENT_GROUP_TOKEN = "group_rac_token_%(token)s"  # nosec

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
    token: ConnectionToken
    logger: BoundLogger

    async def connect(self):
        self.logger = get_logger()
        await self.accept("guacamole")
        await self.channel_layer.group_add(RAC_CLIENT_GROUP, self.channel_name)
        await self.channel_layer.group_add(
            RAC_CLIENT_GROUP_SESSION % {"session": self.scope["session"].session_key},
            self.channel_name,
        )
        await self.init_outpost_connection()

    async def disconnect(self, code):
        self.logger.debug("Disconnecting")
        # Tell the outpost we're disconnecting
        await self.channel_layer.send(
            self.dest_channel_id,
            {
                "type": "event.disconnect",
            },
        )

    @database_sync_to_async
    def init_outpost_connection(self):
        """Initialize guac connection settings"""
        self.token = (
            ConnectionToken.filter_not_expired(token=self.scope["url_route"]["kwargs"]["token"])
            .select_related("endpoint", "provider", "session", "session__user")
            .first()
        )
        if not self.token:
            raise DenyConnection()
        self.provider = self.token.provider
        params = self.token.get_settings()
        self.logger = get_logger().bind(
            endpoint=self.token.endpoint.name, user=self.scope["user"].username
        )
        msg = {
            "type": "event.provider.specific",
            "sub_type": "init_connection",
            "dest_channel_id": self.channel_name,
            "params": params,
            "protocol": self.token.endpoint.protocol,
        }
        query = QueryDict(self.scope["query_string"].decode())
        for key in ["screen_width", "screen_height", "screen_dpi", "audio"]:
            value = query.get(key, None)
            if not value:
                continue
            msg[key] = str(value)
        outposts = Outpost.objects.filter(
            type=OutpostType.RAC,
            providers__in=[self.provider],
        )
        if not outposts.exists():
            self.logger.warning("Provider has no outpost")
            raise DenyConnection()
        for outpost in outposts:
            # Sort all states for the outpost by connection count
            states = sorted(
                OutpostState.for_outpost(outpost),
                key=lambda state: int(state.args.get("active_connections", 0)),
            )
            if len(states) < 1:
                continue
            self.logger.debug("Sending out connection broadcast")
            async_to_sync(self.channel_layer.group_send)(
                OUTPOST_GROUP_INSTANCE % {"instance": states[0].uid.replace("!", ".")},
                msg,
            )
        if self.provider and self.provider.delete_token_on_disconnect:
            self.logger.info("Deleting connection token to prevent reconnect", token=self.token)
            self.token.delete()

    async def receive(self, text_data=None, bytes_data=None):
        """Mirror data received from client to the dest_channel_id
        which is the channel talking to guacd"""
        if self.dest_channel_id == "":
            return
        if self.token.is_expired:
            await self.event_disconnect({"reason": "token_expiry"})
            return
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
        outpost_channel = event.get("outpost_channel")
        if event.get("client_channel") != self.channel_name:
            return
        if self.dest_channel_id != "":
            # We've already selected an outpost channel, so tell the other channel to disconnect
            # This should never happen since we remove ourselves from the broadcast group
            await self.channel_layer.send(
                outpost_channel,
                {
                    "type": "event.disconnect",
                },
            )
            return
        self.logger.debug("Connected to a single outpost instance")
        self.dest_channel_id = outpost_channel
        # Since we have a specific outpost channel now, we can remove
        # ourselves from the global broadcast group
        await self.channel_layer.group_discard(RAC_CLIENT_GROUP, self.channel_name)

    async def event_send(self, event: dict):
        """Handler called by outpost websocket that sends data to this specific
        client connection"""
        if self.token.is_expired:
            await self.event_disconnect({"reason": "token_expiry"})
            return
        await self.send(text_data=event.get("text_data"), bytes_data=event.get("bytes_data"))

    async def event_disconnect(self, event: dict):
        """Disconnect when the session ends"""
        self.logger.info("Disconnecting RAC connection", reason=event.get("reason"))
        await self.close()
