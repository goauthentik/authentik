"""Outpost websocket handler"""
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from time import time
from typing import Any, Dict

from dacite import from_dict
from dacite.data import Data
from django.core.cache import cache
from guardian.shortcuts import get_objects_for_user
from structlog import get_logger

from passbook.core.channels import AuthJsonConsumer
from passbook.outposts.models import Outpost

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
        self.outpost.channels.append(self.channel_name)
        LOGGER.debug("added channel to outpost", channel_name=self.channel_name)
        self.outpost.save()

    # pylint: disable=unused-argument
    def disconnect(self, close_code):
        self.outpost.channels.remove(self.channel_name)
        self.outpost.save()
        LOGGER.debug("removed channel from outpost", channel_name=self.channel_name)

    def receive_json(self, content: Data):
        msg = from_dict(WebsocketMessage, content)
        if msg.instruction == WebsocketMessageInstruction.HELLO:
            cache.set(self.outpost.state_cache_prefix("health"), time(), timeout=60)
            if "version" in msg.args:
                cache.set(
                    self.outpost.state_cache_prefix("version"), msg.args["version"]
                )
        elif msg.instruction == WebsocketMessageInstruction.ACK:
            return

        response = WebsocketMessage(instruction=WebsocketMessageInstruction.ACK)
        self.send_json(asdict(response))

    # pylint: disable=unused-argument
    def event_update(self, event):
        """Event handler which is called by post_save signals"""
        self.send_json(
            asdict(
                WebsocketMessage(instruction=WebsocketMessageInstruction.TRIGGER_UPDATE)
            )
        )
