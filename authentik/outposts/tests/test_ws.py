"""Websocket tests"""
from dataclasses import asdict

from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from authentik import __version__
from authentik.core.tests.utils import create_test_flow
from authentik.outposts.consumer import WebsocketMessage, WebsocketMessageInstruction
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

    async def test_auth_valid(self):
        """Test auth with token"""
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            f"/ws/outpost/{self.outpost.pk}/",
            {b"authorization": f"Bearer {self.token}".encode()},
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

    async def test_send(self):
        """Test sending of Hello"""
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            f"/ws/outpost/{self.outpost.pk}/",
            {b"authorization": f"Bearer {self.token}".encode()},
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to(
            asdict(
                WebsocketMessage(
                    instruction=WebsocketMessageInstruction.HELLO,
                    args={
                        "version": __version__,
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

    async def test_send_ack(self):
        """Test sending of ACK"""
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            f"/ws/outpost/{self.outpost.pk}/",
            {b"authorization": f"Bearer {self.token}".encode()},
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
