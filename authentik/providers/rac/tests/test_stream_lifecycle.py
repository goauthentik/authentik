"""Database-backed authorization lifecycle for live RAC file connections."""

from contextlib import asynccontextmanager
from datetime import timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from channels.db import database_sync_to_async
from django.core.cache import cache
from django.test import TransactionTestCase
from django.utils.timezone import now

from authentik.core.models import AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.rac.consumer_client import RACClientConsumer
from authentik.providers.rac.models import ConnectionToken, Protocols, RACProvider
from authentik.providers.rac.protocol import instruction
from authentik.providers.rac.tests import create_test_device


class TestStreamLifecycle(TransactionTestCase):
    """Token consumption must not be confused with logout or explicit revocation."""

    def setUp(self):
        self.user = create_test_admin_user()
        self.provider = RACProvider.objects.create(
            name="file-transfer", delete_token_on_disconnect=True
        )
        self.device = create_test_device(name="desktop", host="localhost", protocol=Protocols.RDP)
        self.session = Session.objects.create(
            session_key=uuid4().hex, last_ip="127.0.0.1", expiring=False
        )
        self.auth_session = AuthenticatedSession.objects.create(
            session=self.session, user=self.user
        )
        self.token = ConnectionToken.objects.create(
            provider=self.provider,
            device=self.device,
            protocol=Protocols.RDP,
            session=self.auth_session,
            expires=now() + timedelta(hours=1),
        )
        outpost = Outpost.objects.create(name="test-rac", type=OutpostType.RAC)
        outpost.providers.add(self.provider)

    @asynccontextmanager
    async def consumer(self):
        from channels.layers import get_channel_layer

        consumer = RACClientConsumer()
        consumer.channel_layer = get_channel_layer()
        consumer.channel_name = await consumer.channel_layer.new_channel()
        consumer.scope = {
            "user": self.user,
            "session": self.session,
            "query_string": f"connection_id={uuid4()}".encode(),
            "url_route": {"kwargs": {"token": self.token.token}},
        }
        consumer.accept = AsyncMock()
        consumer.send = AsyncMock()
        consumer.close = AsyncMock()
        await consumer.connect()
        try:
            yield consumer
        finally:
            await consumer.disconnect(1000)

    async def test_consuming_one_use_token_preserves_authorized_connection(self):
        async with self.consumer() as consumer:
            self.assertFalse(await ConnectionToken.objects.filter(pk=self.token.pk).aexists())
            self.assertTrue(await consumer.stream_session_active())
            self.assertIsNotNone(await cache.aget(consumer.stream_cache_key))
            self.assertEqual(consumer.token_group, "")
            consumer.close.assert_not_called()

    async def test_connection_uses_token_protocol(self):
        """A device can support multiple protocols; the launch selects this connection."""
        self.token.protocol = Protocols.SSH
        await self.token.asave()
        async with self.consumer() as consumer:
            self.assertEqual(consumer.connection_protocol, Protocols.SSH)
            record = await cache.aget(consumer.stream_cache_key)
            self.assertEqual(record["protocol"], Protocols.SSH)
            self.assertFalse(record["drive"])

    async def test_tunnel_ping_is_echoed_without_reaching_outpost(self):
        async with self.consumer() as consumer:
            consumer.dest_channel_id = "outpost"
            consumer.stream_to_outpost = AsyncMock()
            ping = instruction("", "ping", "1789884000000")
            await consumer.receive(text_data=ping[:8])
            consumer.send.assert_not_called()
            await consumer.receive(text_data=ping[8:])
            consumer.send.assert_awaited_once_with(text_data=ping)
            consumer.stream_to_outpost.assert_not_called()

    async def test_ping_and_input_in_same_message_preserve_input(self):
        async with self.consumer() as consumer:
            consumer.dest_channel_id = "outpost"
            consumer.stream_to_outpost = AsyncMock()
            ping = instruction("", "ping", "1789884000000")
            key = instruction("key", "97", "1")
            await consumer.receive(text_data=ping + key)
            consumer.send.assert_awaited_once_with(text_data=ping)
            consumer.stream_to_outpost.assert_awaited_once_with(key)

    async def test_ping_does_not_keep_expired_authorization_alive(self):
        async with self.consumer() as consumer:
            consumer.dest_channel_id = "outpost"
            consumer.token.expires = now() - timedelta(seconds=1)
            await consumer.receive(text_data=instruction("", "ping", "1789884000000"))
            consumer.send.assert_not_called()
            consumer.close.assert_awaited_once()

    async def test_logout_invalidates_connection_route_and_streams(self):
        async with self.consumer() as consumer:
            key = consumer.stream_cache_key
            await AuthenticatedSession.objects.filter(pk=self.auth_session.pk).adelete()
            event = await consumer.channel_layer.receive(consumer.channel_name)
            self.assertEqual(event["reason"], "session_logout")
            await consumer.event_disconnect(event)
            self.assertIsNone(await cache.aget(key))

    async def test_deleting_reusable_token_revokes_connection(self):
        await RACProvider.objects.filter(pk=self.provider.pk).aupdate(
            delete_token_on_disconnect=False
        )
        async with self.consumer() as consumer:
            self.assertTrue(consumer.token_group)
            await ConnectionToken.objects.filter(pk=self.token.pk).adelete()
            event = await consumer.channel_layer.receive(consumer.channel_name)
            self.assertEqual(event["reason"], "token_delete")
            await consumer.event_disconnect(event)
            self.assertIsNone(await cache.aget(consumer.stream_cache_key))

    async def test_session_expiry_closes_idle_connection(self):
        async with self.consumer() as consumer:
            await Session.objects.filter(pk=self.session.pk).aupdate(
                expiring=True, expires=now() - timedelta(seconds=1)
            )
            await consumer.event_stream_tick({})
            self.assertIsNone(await cache.aget(consumer.stream_cache_key))

    async def test_drive_path_cannot_be_overridden(self):
        self.token.settings = {"drive-path": "/tmp/other", "enable-drive": "false"}
        settings = await database_sync_to_async(self.token.get_settings)()
        self.assertEqual(settings["drive-path"], f"/tmp/connection/{self.token.token}")
        self.assertEqual(settings["enable-drive"], "false")

    async def test_revocation_during_connection_setup_is_not_missed(self):
        await RACProvider.objects.filter(pk=self.provider.pk).aupdate(
            delete_token_on_disconnect=False
        )
        initialize = RACClientConsumer.__dict__["init_outpost_connection"].func

        async def revoke_after_query(consumer):
            await database_sync_to_async(initialize)(consumer)
            await ConnectionToken.objects.filter(pk=self.token.pk).adelete()

        with patch.object(RACClientConsumer, "init_outpost_connection", revoke_after_query):
            async with self.consumer() as consumer:
                consumer.close.assert_awaited_once()
                self.assertEqual(consumer.stream_cache_key, "")
