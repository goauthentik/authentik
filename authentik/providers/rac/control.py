"""Small, bounded control requests addressed to the live RAC connection owner."""

import asyncio
from hashlib import sha256
from uuid import uuid4

from channels.layers import get_channel_layer


def connection_key(tenant: str, token: str, identifier: str) -> str:
    digest = sha256(f"{tenant}/{token}/{identifier}".encode()).hexdigest()
    return f"rac-connection/{digest}"


class StreamRPC:
    """A short-lived reply channel, never used to carry file contents."""

    def __init__(self, owner: str, context: dict, timeout: float = 15) -> None:
        self.layer = get_channel_layer()
        self.owner = owner
        self.context = context
        self.channel = ""
        self.lease = uuid4().hex
        self.timeout = timeout

    async def call(self, action: str, **kwargs) -> dict:
        if not self.channel:
            self.channel = await self.layer.new_channel("rac_control")
        await self.layer.send(
            self.owner,
            {
                **self.context,
                **kwargs,
                "type": "event.stream",
                "action": action,
                "reply": self.channel,
                "lease": self.lease,
            },
        )
        async with asyncio.timeout(self.timeout):
            return await self.layer.receive(self.channel)

    async def close(self) -> None:
        self.channel = ""
