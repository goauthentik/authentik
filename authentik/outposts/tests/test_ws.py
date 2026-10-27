"""Websocket tests"""

from dataclasses import asdict
from datetime import datetime, timedelta

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.utils.timezone import now
from django_channels_postgres.models import GroupChannel

from authentik import authentik_version
from authentik.core.tests.utils import create_test_flow
from authentik.outposts.consumer import (
    WebsocketMessage,
    WebsocketMessageInstruction,
    build_outpost_group,
    build_outpost_group_instance,
)
from authentik.outposts.models import Outpost, OutpostType
from authentik.providers.proxy.models import ProxyProvider
from authentik.root import websocket


class TestOutpostWS(TransactionTestCase):
    """Websocket tests"""

    def setUp(self) -> None:
        self.provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=create_test_flow(),
        )
        self.outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
        )
        self.outpost.providers.add(self.provider)
        self.token = self.outpost.token.key

    async def test_auth(self):
        """Test auth without token"""
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns), f"/ws/outpost/{self.outpost.pk}/"
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_auth_valid(self):
        """Test auth with token"""
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            f"/ws/outpost/{self.outpost.pk}/",
            [(b"authorization", f"Bearer {self.token}".encode())],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_send(self):
        """Test sending of Hello"""
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            f"/ws/outpost/{self.outpost.pk}/",
            [(b"authorization", f"Bearer {self.token}".encode())],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to(
            asdict(
                WebsocketMessage(
                    instruction=WebsocketMessageInstruction.HELLO,
                    args={
                        "version": authentik_version(),
                        "buildHash": "foo",
                        "uuid": "123",
                    },
                )
            )
        )
        response = await communicator.receive_json_from()
        self.assertEqual(
            response, asdict(WebsocketMessage(instruction=WebsocketMessageInstruction.ACK, args={}))
        )
        await communicator.disconnect()

    @database_sync_to_async
    def expire_group_memberships(self, groups: set[str]) -> None:
        """Expire and remove the selected channel group memberships."""
        GroupChannel.objects.filter(group_key__in=groups).update(
            expires=now() - timedelta(seconds=1)
        )
        GroupChannel.delete_expired()

    @database_sync_to_async
    def group_memberships(self, groups: set[str]) -> list[tuple[str, datetime]]:
        """Get expiry times for the selected channel group memberships."""
        return list(
            GroupChannel.objects.filter(group_key__in=groups).values_list("group_key", "expires")
        )

    async def test_hello_refreshes_group_memberships(self):
        """Test that hello messages keep the outpost's channel groups alive."""
        instance_uid = "test-instance"
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            f"/ws/outpost/{self.outpost.pk}/?instance_uuid={instance_uid}",
            [(b"authorization", f"Bearer {self.token}".encode())],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        groups = {
            f"asgi.group.{build_outpost_group(self.outpost.pk)}",
            f"asgi.group.{build_outpost_group_instance(self.outpost.pk, instance_uid)}",
        }
        initial_memberships = await self.group_memberships(groups)
        self.assertEqual({group for group, _ in initial_memberships}, groups)
        self.assertEqual(len(initial_memberships), len(groups))

        await self.expire_group_memberships(groups)
        self.assertEqual(await self.group_memberships(groups), [])

        hello = asdict(
            WebsocketMessage(
                instruction=WebsocketMessageInstruction.HELLO,
                args={"version": authentik_version()},
            )
        )
        await communicator.send_json_to(hello)
        await communicator.receive_json_from()
        first_memberships = await self.group_memberships(groups)
        self.assertEqual({group for group, _ in first_memberships}, groups)
        self.assertEqual(len(first_memberships), len(groups))
        first_refresh = dict(first_memberships)

        await communicator.send_json_to(hello)
        await communicator.receive_json_from()
        second_memberships = await self.group_memberships(groups)
        self.assertEqual({group for group, _ in second_memberships}, groups)
        self.assertEqual(len(second_memberships), len(groups))
        second_refresh = dict(second_memberships)
        for group in groups:
            self.assertGreater(second_refresh[group], first_refresh[group])

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            build_outpost_group_instance(self.outpost.pk, instance_uid),
            {"type": "event.update"},
        )
        self.assertEqual(
            await communicator.receive_json_from(),
            asdict(
                WebsocketMessage(
                    instruction=WebsocketMessageInstruction.TRIGGER_UPDATE,
                )
            ),
        )
        await communicator.disconnect()

    async def test_send_ack(self):
        """Test sending of ACK"""
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            f"/ws/outpost/{self.outpost.pk}/",
            [(b"authorization", f"Bearer {self.token}".encode())],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to(
            asdict(
                WebsocketMessage(
                    instruction=WebsocketMessageInstruction.ACK,
                    args={},
                )
            )
        )
        await communicator.disconnect()
