"""RAC Client consumer"""

import asyncio
import json
from hashlib import sha256
from http import HTTPStatus
from time import monotonic
from uuid import UUID, uuid4

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.exceptions import ChannelFull, DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django.http.request import QueryDict
from django.utils.timezone import now
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import AuthenticatedSession
from authentik.outposts.consumer import build_outpost_group_instance
from authentik.outposts.models import Outpost, OutpostState, OutpostType
from authentik.providers.rac.control import connection_key
from authentik.providers.rac.guacamole import (
    GuacamoleInstructionParser,
    GuacamoleProtocolError,
)
from authentik.providers.rac.models import ConnectionToken, RACProvider
from authentik.providers.rac.protocol import (
    CONTROL_MAX_REQUESTS,
    CONTROL_TIMEOUT,
    UTF16_MAX,
    InstructionParser,
    instruction,
    valid_file_path,
)

TRANSFER_ID_LENGTH = 36


def build_rac_client_group() -> str:
    """
    Global broadcast group, which messages are sent to when the outpost connects back
    to authentik for a specific connection
    The `RACClientConsumer` consumer adds itself to this group on connection,
    and removes itself once it has been assigned a specific outpost channel
    """
    return sha256(f"{connection.schema_name}/group_rac_client".encode()).hexdigest()


def build_rac_client_group_session(session_key: str) -> str:
    """
    A group for all connections in a given authentik session ID
    A disconnect message is sent to this group when the session expires/is deleted
    """
    return sha256(f"{connection.schema_name}/group_rac_client_{session_key}".encode()).hexdigest()


def build_rac_client_group_token(token: str) -> str:
    """
    A group for all connections with a specific token, which in almost all cases
    is just one connection, however this is used to disconnect the connection
    when the token is deleted
    """
    return sha256(f"{connection.schema_name}/group_rac_token_{token}".encode()).hexdigest()


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
    guacamole_parser: GuacamoleInstructionParser

    async def connect(self):
        self.logger = get_logger()
        self.stream_disconnected = False
        self.control_requests = {}
        self.bulk_transfers = set()
        self.bulk_requests = {}
        self.blocked_file_streams = set()
        self.stream_monitor = None
        self.stream_cache_key = ""
        self.token_group = ""
        self.session_group = build_rac_client_group_session(self.scope["session"].session_key)
        self.guacamole_parser = GuacamoleInstructionParser()
        self.remote_parser = InstructionParser()
        self.connection_id = ""
        self.allowed_outpost_users = set()
        query = QueryDict(self.scope["query_string"].decode())
        if query.get("connection_id"):
            try:
                self.connection_id = str(UUID(query["connection_id"]))
            except ValueError as exc:
                raise DenyConnection() from exc
        await self.accept("guacamole")
        await self.channel_layer.group_add(build_rac_client_group(), self.channel_name)
        await self.channel_layer.group_add(
            self.session_group,
            self.channel_name,
        )
        await self.init_outpost_connection()
        # A one-use token is deliberately consumed by init_outpost_connection.
        # Subscribe after consumption, while all other token deletions revoke
        # reusable connections through the existing signal.
        if not self.provider.delete_token_on_disconnect:
            self.token_group = build_rac_client_group_token(self.rac_token)
            await self.channel_layer.group_add(self.token_group, self.channel_name)
            # Cover revocation between the authorization query and subscribing.
            # Later deletions are delivered through the token group.
            if not await ConnectionToken.objects.filter(pk=self.token.pk).aexists():
                await self.event_disconnect({"reason": "token_delete"})
                return
        if self.connection_id:
            self.stream_identity = {
                "user": str(self.scope["user"].pk),
                "session": self.scope["session"].session_key,
                "tenant": connection.schema_name,
            }
            self.stream_cache_key = connection_key(
                self.stream_identity["tenant"],
                self.rac_token,
                self.connection_id,
            )
            if not await cache.aadd(
                self.stream_cache_key,
                self.connection_record(),
                timeout=90,
            ):
                self.stream_cache_key = ""
                await self.close(code=1008)
                return
            self.stream_monitor = asyncio.create_task(self.monitor_streams())

    async def disconnect(self, code):
        self.logger.info("RAC client WebSocket disconnected", code=code)
        self.stream_disconnected = True
        await self.close_streams()
        await self.channel_layer.group_discard(build_rac_client_group(), self.channel_name)
        await self.channel_layer.group_discard(self.session_group, self.channel_name)
        if self.token_group:
            await self.channel_layer.group_discard(self.token_group, self.channel_name)
        if self.dest_channel_id:
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
            ConnectionToken.objects.filter(
                token=self.scope["url_route"]["kwargs"]["token"],
                session__session__session_key=self.scope["session"].session_key,
            )
            .select_related("device", "provider", "session", "session__user")
            .first()
        )
        if not self.token:
            raise DenyConnection()
        if self.token.is_expired or self.token.session.user_id != self.scope["user"].pk:
            raise DenyConnection()
        self.rac_token = self.token.token
        self.provider = self.token.provider
        params = self.token.get_settings()
        self.connection_settings = params
        self.connection_protocol = self.token.protocol
        self.logger = get_logger().bind(
            device=self.token.device.name, user=self.scope["user"].username
        )
        msg = {
            "type": "event.provider.specific",
            "sub_type": "init_connection",
            "dest_channel_id": self.channel_name,
            "params": params,
            "protocol": self.token.protocol,
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
            self.allowed_outpost_users.add(str(outpost.user.pk))
            # Sort all states for the outpost by connection count
            states = sorted(
                OutpostState.for_outpost(outpost),
                key=lambda state: int(state.args.get("active_connections", 0)),
            )
            if len(states) < 1:
                continue
            self.logger.debug("Sending out connection broadcast")
            group = build_outpost_group_instance(outpost.pk, states[0].uid)
            async_to_sync(self.channel_layer.group_send)(group, msg)
        if self.provider and self.provider.delete_token_on_disconnect:
            self.logger.info("Deleting connection token to prevent reconnect", token=self.token)
            self.token.delete()

    async def receive(self, text_data=None, bytes_data=None):
        """Preserve upstream tunnel handling and route negotiated file streams."""
        if self.token.is_expired:
            await self.event_disconnect({"reason": "token_expiry"})
            return
        # Browser tunnel messages are text-only, as in the upstream consumer.
        if text_data is None:
            return
        try:
            instructions = self.guacamole_parser.feed(text_data)
            responses, forwarded = self.guacamole_parser.split_internal(instructions)
        except GuacamoleProtocolError as exc:
            self.logger.debug("Ignoring malformed Guacamole protocol data", error=str(exc))
            return

        for response in responses:
            await self.send(text_data=response)

        if not forwarded or not self.dest_channel_id:
            return
        try:
            pending = []
            for raw, elements in instructions:
                opcode = elements[0]
                if not opcode:
                    continue
                stream = elements[1] if len(elements) > 1 else ""
                if opcode in {"file", "put", "get"}:
                    if stream:
                        self.blocked_file_streams.add(stream)
                    continue
                if opcode in {"blob", "ack", "end"} and stream in self.blocked_file_streams:
                    if opcode == "end":
                        self.blocked_file_streams.discard(stream)
                    continue
                pending.append(raw)
            if pending:
                await self.stream_to_outpost("".join(pending))
        except ValueError, OSError, ChannelFull:
            await self.event_disconnect({"reason": "invalid_stream_or_channel_failure"})

    async def event_outpost_connected(self, event: dict):
        """Handle event broadcasted from outpost consumer, and check if they
        created a connection for us"""
        outpost_channel = event.get("outpost_channel")
        if event.get("client_channel") != self.channel_name:
            return
        if event.get("outpost_user") not in self.allowed_outpost_users:
            await self.channel_layer.send(outpost_channel, {"type": "event.disconnect"})
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
        self.outpost_user = event.get("outpost_user")
        if self.stream_cache_key:
            await cache.aset(self.stream_cache_key, self.connection_record(), timeout=90)
        # Since we have a specific outpost channel now, we can remove
        # ourselves from the global broadcast group
        await self.channel_layer.group_discard(build_rac_client_group(), self.channel_name)

    async def event_send(self, event: dict):
        """Handler called by outpost websocket that sends data to this specific
        client connection"""
        if self.token.is_expired:
            await self.event_disconnect({"reason": "token_expiry"})
            return
        if event.get("outpost_channel") != self.dest_channel_id:
            return
        try:
            data = event.get("text_data")
            if data is None:
                data = event.get("bytes_data")
            pending = []
            for elements in self.remote_parser.feed(data):
                opcode = elements[0]
                stream = elements[1] if len(elements) > 1 else ""
                if opcode in {"file", "body"}:
                    if stream:
                        self.blocked_file_streams.add(stream)
                    continue
                if opcode == "filesystem":
                    continue
                if opcode in {"blob", "ack", "end"} and stream in self.blocked_file_streams:
                    if opcode == "end":
                        self.blocked_file_streams.discard(stream)
                    continue
                pending.append(instruction(*elements))
            if pending:
                await self.stream_to_client("".join(pending))
        except ValueError, OSError, ChannelFull:
            await self.event_disconnect({"reason": "invalid_stream_or_channel_failure"})

    async def stream_to_client(self, data: str) -> None:
        if not self.stream_disconnected:
            if not data.isascii() and any(ord(char) > UTF16_MAX for char in data):
                data = "".join(
                    instruction(*elements, utf16=True)
                    for elements in InstructionParser().feed(data)
                )
            await self.send(text_data=data)

    async def stream_to_outpost(self, data: str) -> None:
        if not self.dest_channel_id:
            raise OSError("Outpost is not connected")
        await self.channel_layer.send(
            self.dest_channel_id,
            {
                "type": "event.send",
                "text_data": data,
            },
        )

    async def event_stream(self, event: dict) -> None:
        """Recheck the live owner's identity; cache metadata grants no authority."""
        if (
            self.token.is_expired
            or event.get("connection") != self.connection_id
            or event.get("token") != self.rac_token
            or any(event.get(key) != value for key, value in self.stream_identity.items())
        ):
            await self.channel_layer.send(
                event["reply"],
                {
                    "status": 404,
                    "error": "RAC connection is unavailable",
                },
            )
            return
        try:
            if event.get("action") in {"prepare", "finish", "cancel"}:
                await self.request_bulk(event)
                return
            if event.get("action") == "list":
                await self.request_directory(event)
                return
            await self.channel_layer.send(event["reply"], {"status": 400})
        except OSError, ChannelFull:
            await self.channel_layer.send(event["reply"], {"status": 503})

    async def request_directory(self, event: dict) -> None:
        if (
            self.connection_protocol != "rdp"
            or self.connection_settings.get("enable-drive") != "true"
            or not self.dest_channel_id
            or not valid_file_path(event.get("path", ""))
        ):
            await self.channel_layer.send(event["reply"], {"status": 400})
            return
        self.control_requests = {
            key: value
            for key, value in self.control_requests.items()
            if monotonic() - value[1] < CONTROL_TIMEOUT
        }
        if len(self.control_requests) >= CONTROL_MAX_REQUESTS:
            await self.channel_layer.send(event["reply"], {"status": 429})
            return
        identifier = uuid4().hex
        self.control_requests[identifier] = (event["reply"], monotonic())
        await self.channel_layer.send(
            self.dest_channel_id,
            {
                "type": "event.file.list",
                "payload": json.dumps(
                    {
                        "request": identifier,
                        "path": event["path"],
                        "cursor": event.get("cursor", ""),
                    }
                ),
            },
        )

    async def event_file_list_reply(self, event: dict) -> None:
        if event.get("outpost_channel") != self.dest_channel_id:
            return
        identifier = event["payload"].get("request")
        if not isinstance(identifier, str):
            return
        pending = self.control_requests.pop(identifier, None)
        if pending:
            await self.channel_layer.send(
                pending[0],
                {
                    "status": event["payload"].get("status", 503),
                    "entries": event["payload"].get("entries", []),
                    "cursor": event["payload"].get("cursor", ""),
                },
            )

    async def request_bulk(self, event: dict) -> None:
        action = event["action"]
        transfer = event.get("transfer", "")
        if (
            self.connection_protocol != "rdp"
            or self.connection_settings.get("enable-drive") != "true"
            or not self.dest_channel_id
            or not isinstance(transfer, str)
            or len(transfer) != TRANSFER_ID_LENGTH
        ):
            await self.channel_layer.send(event["reply"], {"status": 404})
            return
        if action == "prepare":
            direction = event.get("direction")
            if (
                direction not in {"upload", "download"}
                or self.connection_settings.get(f"rac-allow-{direction}") != "true"
                or not valid_file_path(event.get("path", ""))
            ):
                await self.channel_layer.send(event["reply"], {"status": 403})
                return
        elif transfer not in self.bulk_transfers:
            await self.channel_layer.send(event["reply"], {"status": 404})
            return
        identifier = uuid4().hex
        self.control_requests[identifier] = (event["reply"], monotonic())
        self.bulk_requests[identifier] = (action, transfer)
        await self.channel_layer.send(
            self.dest_channel_id,
            {
                "type": "event.file.bulk",
                "payload": json.dumps(
                    {
                        "request": identifier,
                        "action": action,
                        "id": transfer,
                        "path": event.get("path", ""),
                        "direction": event.get("direction", ""),
                        "size": event.get("size", 0),
                        "tenant": self.stream_identity["tenant"],
                    }
                ),
            },
        )
        if action == "prepare":
            self.bulk_transfers.add(transfer)
        elif action == "cancel":
            self.bulk_transfers.discard(transfer)

    async def event_file_bulk_reply(self, event: dict) -> None:
        if event.get("outpost_channel") != self.dest_channel_id:
            return
        closed = event["payload"].get("id")
        if isinstance(closed, str) and closed in self.bulk_transfers:
            self.bulk_transfers.discard(closed)
            await cache.adelete(f"rac-bulk/{closed}")
            await cache.adelete(f"rac-bulk-owner/{closed}")
            await self.stream_to_client(
                instruction(
                    "authentik-bulk",
                    closed,
                    "ok" if event["payload"].get("status") == HTTPStatus.OK else "error",
                )
            )
        identifier = event["payload"].get("request")
        if not isinstance(identifier, str):
            return
        operation = self.bulk_requests.pop(identifier, None)
        if operation and (
            event["payload"].get("status") != HTTPStatus.OK or operation[0] == "finish"
        ):
            self.bulk_transfers.discard(operation[1])
        pending = self.control_requests.pop(identifier, None)
        if pending:
            await self.channel_layer.send(
                pending[0],
                {
                    "status": event["payload"].get("status", 503),
                    "size": event["payload"].get("size", 0),
                },
            )

    async def monitor_streams(self) -> None:
        while True:
            await asyncio.sleep(15)
            await self.channel_layer.send(self.channel_name, {"type": "event.stream.tick"})

    @database_sync_to_async
    def stream_session_active(self) -> bool:
        return AuthenticatedSession.objects.filter(
            Q(session__expiring=False) | Q(session__expires__gt=now()),
            pk=self.token.session_id,
            user_id=self.scope["user"].pk,
            user__is_active=True,
            session__session_key=self.scope["session"].session_key,
        ).exists()

    async def event_stream_tick(self, event: dict) -> None:
        if not self.stream_cache_key:
            return
        if self.token.is_expired or not await self.stream_session_active():
            await self.event_disconnect({"reason": "session_expiry"})
            return
        await cache.aset(
            self.stream_cache_key,
            self.connection_record(),
            timeout=90,
        )
        for transfer in self.bulk_transfers:
            await cache.atouch(f"rac-bulk/{transfer}", timeout=90)
            await cache.atouch(f"rac-bulk-owner/{transfer}", timeout=90)

    def connection_record(self) -> dict:
        return {
            **self.stream_identity,
            "channel": self.channel_name,
            "protocol": self.connection_protocol,
            "drive": self.connection_settings.get("enable-drive") == "true",
            "upload": self.connection_settings.get("rac-allow-upload") == "true",
            "download": self.connection_settings.get("rac-allow-download") == "true",
            "outpost_user": getattr(self, "outpost_user", None),
        }

    async def close_streams(self) -> None:
        if self.dest_channel_id:
            for transfer in getattr(self, "bulk_transfers", set()):
                await cache.adelete(f"rac-bulk/{transfer}")
                await cache.adelete(f"rac-bulk-owner/{transfer}")
                try:
                    await self.channel_layer.send(
                        self.dest_channel_id,
                        {
                            "type": "event.file.bulk",
                            "payload": json.dumps(
                                {"request": uuid4().hex, "action": "cancel", "id": transfer}
                            ),
                        },
                    )
                except OSError, ChannelFull:
                    pass
        self.bulk_transfers = set()
        self.bulk_requests = {}
        for reply, _ in getattr(self, "control_requests", {}).values():
            try:
                await self.channel_layer.send(reply, {"status": 404})
            except OSError, ChannelFull:
                pass
        self.control_requests = {}
        if self.stream_monitor:
            self.stream_monitor.cancel()
            await asyncio.gather(self.stream_monitor, return_exceptions=True)
            self.stream_monitor = None
        if self.stream_cache_key:
            await cache.adelete(self.stream_cache_key)
            self.stream_cache_key = ""

    async def event_disconnect(self, event: dict):
        """Disconnect when the session ends"""
        if event.get("outpost_channel") and event["outpost_channel"] != self.dest_channel_id:
            return
        self.logger.info("Disconnecting RAC connection", reason=event.get("reason"))
        await self.close_streams()
        await self.close()
