"""Outpost websocket handler"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import IntEnum
from hashlib import sha256
from typing import Any
from uuid import UUID

from asgiref.sync import async_to_sync
from channels.exceptions import DenyConnection
from channels.generic.websocket import JsonWebsocketConsumer
from dacite.core import from_dict
from dacite.data import Data
from django.db import connection
from django.http.request import QueryDict
from guardian.shortcuts import get_objects_for_user
from structlog.stdlib import BoundLogger, get_logger

from authentik.outposts.apps import GAUGE_OUTPOSTS_CONNECTED, GAUGE_OUTPOSTS_LAST_UPDATE
from authentik.outposts.models import OUTPOST_HELLO_INTERVAL, Outpost, OutpostState


def build_outpost_group(outpost_pk: str | UUID) -> str:
    return sha256(f"{connection.schema_name}/group_outpost_{str(outpost_pk)}".encode()).hexdigest()


def build_outpost_group_instance(outpost_pk: str | UUID, instance: str) -> str:
    return sha256(
        f"{connection.schema_name}/group_outpost_{str(outpost_pk)}_{instance}".encode()
    ).hexdigest()


class WebsocketMessageInstruction(IntEnum):
    """Commands which can be triggered over Websocket"""

    # Simple message used by either side when a message is acknowledged
    ACK = 0

    # Message used by outposts to report their alive status
    HELLO = 1

    # Message sent by us to trigger an Update
    TRIGGER_UPDATE = 2

    # Provider specific message
    PROVIDER_SPECIFIC = 3

    # Session ended
    SESSION_END = 4


@dataclass(slots=True)
class WebsocketMessage:
    """Complete Websocket Message that is being sent"""

    instruction: int
    args: dict[str, Any] = field(default_factory=dict)


class OutpostConsumer(JsonWebsocketConsumer):
    """Handler for Outposts that connect over websockets for health checks and live updates"""

    outpost: Outpost | None = None
    logger: BoundLogger

    instance_uid: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger()

    def connect(self):
        uuid = self.scope["url_route"]["kwargs"]["pk"]
        user = self.scope["user"]
        self.outpost: Outpost | None = (
            get_objects_for_user(user, "authentik_outposts.view_outpost").filter(pk=uuid).first()
        )
        if self.outpost is None:
            raise DenyConnection()
        self.logger = self.logger.bind(outpost=self.outpost)
        try:
            self.accept()
        except RuntimeError as exc:
            self.logger.warning("runtime error during accept", exc=exc)
            raise DenyConnection() from None
        query = QueryDict(self.scope["query_string"].decode())
        self.instance_uid = query.get("instance_uuid", self.channel_name)
        async_to_sync(self.channel_layer.group_add)(
            build_outpost_group(self.outpost.pk), self.channel_name
        )
        async_to_sync(self.channel_layer.group_add)(
            build_outpost_group_instance(self.outpost.pk, self.instance_uid),
            self.channel_name,
        )
        GAUGE_OUTPOSTS_CONNECTED.labels(
            tenant=connection.schema_name,
            outpost=self.outpost.name,
            uid=self.instance_uid,
            expected=self.outpost.config.kubernetes_replicas,
        ).inc()

    def disconnect(self, code):
        if self.outpost:
            async_to_sync(self.channel_layer.group_discard)(
                build_outpost_group(self.outpost.pk), self.channel_name
            )
            if self.instance_uid:
                async_to_sync(self.channel_layer.group_discard)(
                    build_outpost_group_instance(self.outpost.pk, self.instance_uid),
                    self.channel_name,
                )
        if self.outpost and self.instance_uid:
            GAUGE_OUTPOSTS_CONNECTED.labels(
                tenant=connection.schema_name,
                outpost=self.outpost.name,
                uid=self.instance_uid,
                expected=self.outpost.config.kubernetes_replicas,
            ).dec()

    def receive_json(self, content: Data, **kwargs):
        msg = from_dict(WebsocketMessage, content)
        if not self.outpost:
            raise DenyConnection()

        state = OutpostState.for_instance_uid(self.outpost, self.instance_uid)
        state.last_seen = datetime.now()
        state.hostname = msg.args.pop("hostname", "")

        if msg.instruction == WebsocketMessageInstruction.HELLO:
            state.version = msg.args.pop("version", None)
            state.build_hash = msg.args.pop("buildHash", "")
            state.golang_version = msg.args.pop("golangVersion", "")
            state.openssl_enabled = msg.args.pop("opensslEnabled", False)
            state.openssl_version = msg.args.pop("opensslVersion", "")
            state.fips_enabled = msg.args.pop("fipsEnabled", False)
            state.args.update(msg.args)
        elif msg.instruction == WebsocketMessageInstruction.ACK:
            return
        GAUGE_OUTPOSTS_LAST_UPDATE.labels(
            tenant=connection.schema_name,
            outpost=self.outpost.name,
            uid=self.instance_uid or "",
            version=state.version or "",
        ).set_to_current_time()
        state.save(timeout=OUTPOST_HELLO_INTERVAL * 1.5)

        response = WebsocketMessage(instruction=WebsocketMessageInstruction.ACK)
        self.send_json(asdict(response))

    def event_update(self, event):  # pragma: no cover
        """Event handler which is called by post_save signals, Send update instruction"""
        self.send_json(
            asdict(WebsocketMessage(instruction=WebsocketMessageInstruction.TRIGGER_UPDATE))
        )

    def event_session_end(self, event):
        """Event handler which is called when a session is ended"""
        self.send_json(
            asdict(
                WebsocketMessage(instruction=WebsocketMessageInstruction.SESSION_END, args=event)
            )
        )

    def event_provider_specific(self, event):
        """Event handler which can be called by provider-specific
        implementations to send specific messages to the outpost"""
        self.send_json(
            asdict(
                WebsocketMessage(
                    instruction=WebsocketMessageInstruction.PROVIDER_SPECIFIC, args=event
                )
            )
        )
