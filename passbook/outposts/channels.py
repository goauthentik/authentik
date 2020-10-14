"""Outpost websocket handler"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict

from dacite import from_dict
from dacite.data import Data
from guardian.shortcuts import get_objects_for_user
from structlog import get_logger

from passbook.core.channels import AuthJsonConsumer
from passbook.outposts.models import OUTPOST_HELLO_INTERVAL, Outpost, OutpostState

LOGGER = get_logger()


class WebsocketMessageInstruction(IntEnum):
    """Commands which can be triggered over Websocket"""

    # Simple message used by either side when a message is acknowledged
    ACK = 0

    # Message used by outposts to report their alive status
    HELLO = 1

    # Message sent by us to trigger an Update
    TRIGGER_UPDATE = 2


@dataclass
class WebsocketMessage:
    """Complete Websocket Message that is being sent"""

    instruction: int
    args: Dict[str, Any] = field(default_factory=dict)


class OutpostConsumer(AuthJsonConsumer):
    """Handler for Outposts that connect over websockets for health checks and live updates"""

    outpost: Outpost

    def connect(self):
        if not super().connect():
            return
        uuid = self.scope["url_route"]["kwargs"]["pk"]
        outpost = get_objects_for_user(
            self.user, "passbook_outposts.view_outpost"
        ).filter(pk=uuid)
        if not outpost.exists():
            self.close()
            return
        self.accept()
        self.outpost = outpost.first()
        OutpostState(
            uid=self.channel_name, last_seen=datetime.now(), _outpost=self.outpost
        ).save(timeout=OUTPOST_HELLO_INTERVAL * 1.5)
        LOGGER.debug("added channel to cache", channel_name=self.channel_name)

    # pylint: disable=unused-argument
    def disconnect(self, close_code):
        OutpostState.for_channel(self.outpost, self.channel_name).delete()
        LOGGER.debug("removed channel from cache", channel_name=self.channel_name)

    def receive_json(self, content: Data):
        msg = from_dict(WebsocketMessage, content)
        state = OutpostState(
            uid=self.channel_name,
            last_seen=datetime.now(),
            _outpost=self.outpost,
        )
        if msg.instruction == WebsocketMessageInstruction.HELLO:
            state.version = msg.args.get("version", None)
        elif msg.instruction == WebsocketMessageInstruction.ACK:
            return
        state.save(timeout=OUTPOST_HELLO_INTERVAL * 1.5)

        response = WebsocketMessage(instruction=WebsocketMessageInstruction.ACK)
        self.send_json(asdict(response))

    # pylint: disable=unused-argument
    def event_update(self, event):
        """Event handler which is called by post_save signals, Send update instruction"""
        self.send_json(
            asdict(
                WebsocketMessage(instruction=WebsocketMessageInstruction.TRIGGER_UPDATE)
            )
        )
