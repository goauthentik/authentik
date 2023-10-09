"""Outpost websocket handler"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Optional

from channels.exceptions import DenyConnection
from dacite.core import from_dict
from dacite.data import Data
from guardian.shortcuts import get_objects_for_user
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.channels import AuthJsonConsumer
from authentik.outposts.apps import GAUGE_OUTPOSTS_CONNECTED, GAUGE_OUTPOSTS_LAST_UPDATE
from authentik.outposts.models import OUTPOST_HELLO_INTERVAL, Outpost, OutpostState


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


@dataclass(slots=True)
class WebsocketMessage:
    """Complete Websocket Message that is being sent"""

    instruction: int
    args: dict[str, Any] = field(default_factory=dict)


class OutpostConsumer(AuthJsonConsumer):
    """Handler for Outposts that connect over websockets for health checks and live updates"""

    outpost: Optional[Outpost] = None
    logger: BoundLogger

    last_uid: Optional[str] = None

    first_msg = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger()

    def connect(self):
        super().connect()
        uuid = self.scope["url_route"]["kwargs"]["pk"]
        outpost = (
            get_objects_for_user(self.user, "authentik_outposts.view_outpost")
            .filter(pk=uuid)
            .first()
        )
        if not outpost:
            raise DenyConnection()
        self.logger = self.logger.bind(outpost=outpost)
        try:
            self.accept()
        except RuntimeError as exc:
            self.logger.warning("runtime error during accept", exc=exc)
            raise DenyConnection()
        self.outpost = outpost
        self.last_uid = self.channel_name

    def disconnect(self, code):
        if self.outpost and self.last_uid:
            state = OutpostState.for_instance_uid(self.outpost, self.last_uid)
            if self.channel_name in state.channel_ids:
                state.channel_ids.remove(self.channel_name)
                state.save()
            GAUGE_OUTPOSTS_CONNECTED.labels(
                outpost=self.outpost.name,
                uid=self.last_uid,
                expected=self.outpost.config.kubernetes_replicas,
            ).dec()
        self.logger.debug(
            "removed outpost instance from cache",
            instance_uuid=self.last_uid,
        )

    def receive_json(self, content: Data):
        msg = from_dict(WebsocketMessage, content)
        uid = msg.args.get("uuid", self.channel_name)
        self.last_uid = uid

        if not self.outpost:
            raise DenyConnection()

        state = OutpostState.for_instance_uid(self.outpost, uid)
        if self.channel_name not in state.channel_ids:
            state.channel_ids.append(self.channel_name)
        state.last_seen = datetime.now()
        state.hostname = msg.args.get("hostname", "")

        if not self.first_msg:
            GAUGE_OUTPOSTS_CONNECTED.labels(
                outpost=self.outpost.name,
                uid=self.last_uid,
                expected=self.outpost.config.kubernetes_replicas,
            ).inc()
            self.logger.debug(
                "added outpost instance to cache",
                instance_uuid=self.last_uid,
            )
            self.first_msg = True

        if msg.instruction == WebsocketMessageInstruction.HELLO:
            state.version = msg.args.get("version", None)
            state.build_hash = msg.args.get("buildHash", "")
        elif msg.instruction == WebsocketMessageInstruction.ACK:
            return
        GAUGE_OUTPOSTS_LAST_UPDATE.labels(
            outpost=self.outpost.name,
            uid=self.last_uid or "",
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
