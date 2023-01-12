"""RAC consumer"""
from asyncio import create_task

from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from guacamole.client import GuacamoleClient

from authentik.core.models import Application
from authentik.enterprise.rac.models import RACProvider


class GuacamoleConsumer(AsyncWebsocketConsumer):
    client: GuacamoleClient
    closed: bool

    async def connect(self):
        super().connect()
        provider = await self.pre_connect()
        await self.accept("guacamole")
        self.closed = False
        # TODO: Send traffic via ws tunnel to outpost?
        self.client = GuacamoleClient("127.0.0.1", 4822)
        self.client.handshake(
            protocol=provider.protocol, hostname=provider.host, **provider.settings
        )
        self.task = create_task(self.transferer)

    async def transferer(self):
        while True:
            try:
                data = self.client.receive()
                if data:
                    self.send(data)
            except TimeoutError:
                continue
            if self.closed:
                break

    @database_sync_to_async
    def pre_connect(self):
        app_slug = self.scope["url_route"]["kwargs"]["app"]
        app = Application.objects.filter(slug=app_slug, provider__isnull=False).first()
        if not app:
            raise DenyConnection()
        # TODO: Check policy access
        # TODO: ensure provider is correct type
        provider: RACProvider = app.provider
        return provider

    def disconnect(self, code):
        self.closed = True
        self.client.close()
        self.task.cancel()

    def receive(self, text_data=None, bytes_data=None):
        self.client.send(text_data)
