"""Websocket tests"""

from dataclasses import asdict
from unittest.mock import patch, MagicMock
import asyncio

from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator, ChannelsLiveServerTestCase
from channels.layers import InMemoryChannelLayer
from django.test import TransactionTestCase

from authentik import __version__
from authentik.core.tests.utils import create_test_flow
from authentik.outposts.consumer import (
    WebsocketMessage,
    WebsocketMessageInstruction,
    OUTPOST_GROUP,
    OUTPOST_GROUP_INSTANCE,
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
        self.channel_layer_patcher = patch('channels.layers.get_channel_layer', 
                                         return_value=InMemoryChannelLayer())
        self.channel_layer_patcher.start()
        self.addCleanup(self.channel_layer_patcher.stop)

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

    async def test_connection_setup_failure(self):
        """Test handling of connection setup failure"""
        # Create a mock that will raise an exception during setup
        with patch('authentik.outposts.consumer.OutpostConsumer.accept') as mock_accept:
            mock_accept.side_effect = RuntimeError("Test error")
            communicator = WebsocketCommunicator(
                URLRouter(websocket.websocket_urlpatterns),
                f"/ws/outpost/{self.outpost.pk}/",
                {b"authorization": f"Bearer {self.token}".encode()},
            )
            connected, _ = await communicator.connect()
            self.assertFalse(connected)

    async def test_connection_cleanup(self):
        """Test proper cleanup of failed connection"""
        # Create a mock that will raise an exception during setup
        with patch('authentik.outposts.consumer.OutpostConsumer.accept') as mock_accept:
            mock_accept.side_effect = RuntimeError("Test error")
            with patch('authentik.outposts.consumer.OutpostConsumer.close') as mock_close:
                # Don't actually try to establish a websocket connection
                with patch('authentik.outposts.consumer.async_to_sync'):
                    communicator = WebsocketCommunicator(
                        URLRouter(websocket.websocket_urlpatterns),
                        f"/ws/outpost/{self.outpost.pk}/",
                        {b"authorization": f"Bearer {self.token}".encode()},
                    )
                    communicator.scope["channel_name"] = "test_channel_name"
                    
                    # Use a short timeout since we expect the connection to fail
                    connected, _ = await communicator.connect(timeout=1)
                    self.assertFalse(connected)
                    # Wait a bit for the cleanup to happen
                    await asyncio.sleep(0.1)
                    # Verify close was called
                    mock_close.assert_called_once()
                    # Ensure we properly close the communicator
                    await communicator.disconnect()

    async def test_connection_success(self):
        """Test successful connection setup"""
        # Mock group_add for verification
        mock_group_add = MagicMock()
        
        with patch('authentik.outposts.consumer.async_to_sync') as mock_async_to_sync:
            def mock_async_to_sync_fn(func):
                if func.__name__ == 'group_add':
                    return mock_group_add
                return func
            mock_async_to_sync.side_effect = mock_async_to_sync_fn
            
            communicator = WebsocketCommunicator(
                URLRouter(websocket.websocket_urlpatterns),
                f"/ws/outpost/{self.outpost.pk}/",
                {b"authorization": f"Bearer {self.token}".encode()},
            )
            communicator.scope["channel_name"] = "test_channel_name"
            
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            
            # Verify group_add was called with correct arguments
            mock_group_add.assert_any_call(
                OUTPOST_GROUP % {"outpost_pk": str(self.outpost.pk)}, 
                "test_channel_name"
            )
            
            await communicator.disconnect()

    async def test_connection_with_query_params(self):
        """Test connection with query parameters"""
        instance_uuid = "test-instance-123"
        # Mock group_add for verification
        mock_group_add = MagicMock()
        
        with patch('authentik.outposts.consumer.async_to_sync') as mock_async_to_sync:
            def mock_async_to_sync_fn(func):
                if func.__name__ == 'group_add':
                    return mock_group_add
                return func
            mock_async_to_sync.side_effect = mock_async_to_sync_fn
            
            communicator = WebsocketCommunicator(
                URLRouter(websocket.websocket_urlpatterns),
                f"/ws/outpost/{self.outpost.pk}/?instance_uuid={instance_uuid}",
                {b"authorization": f"Bearer {self.token}".encode()},
            )
            communicator.scope["channel_name"] = "test_channel_name"
            
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            
            # Verify group_add was called with correct arguments for both groups
            mock_group_add.assert_any_call(
                OUTPOST_GROUP % {"outpost_pk": str(self.outpost.pk)},
                "test_channel_name"
            )
            mock_group_add.assert_any_call(
                OUTPOST_GROUP_INSTANCE % {
                    "outpost_pk": str(self.outpost.pk),
                    "instance": instance_uuid
                },
                "test_channel_name"
            )
            
            await communicator.disconnect()
