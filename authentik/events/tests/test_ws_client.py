from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from structlog.testing import capture_logs

from authentik.core.tests.utils import create_test_user
from authentik.events.models import (
    Event,
    EventAction,
    Notification,
    NotificationTransport,
    TransportMode,
)
from authentik.lib.generators import generate_id
from authentik.root import websocket


class TestClientWS(TransactionTestCase):
    def setUp(self):
        self.user = create_test_user()

    async def test_unauthenticated(self):
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns), "/ws/client/"
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_non_utf8_headers(self):
        """Header values that aren't valid UTF-8 don't break the connection"""
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            "/ws/client/",
            headers=[(b"user-agent", b"Mozilla/5.0 Meta\xa0AI"), (b"x-forwarded-for", b"\xff")],
        )
        communicator.scope["user"] = self.user
        with capture_logs() as logs:
            connected, _ = await communicator.connect()
        self.assertTrue(connected)
        log = next(log for log in logs if log.get("scheme") == "ws")
        self.assertEqual(log["user_agent"], "Mozilla/5.0 Meta\\xa0AI")
        self.assertEqual(log["remote"], "\\xff")
        await communicator.disconnect()

    async def test_notification(self):
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns), "/ws/client/"
        )
        communicator.scope["user"] = self.user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        transport = await NotificationTransport.objects.acreate(
            name=generate_id(), mode=TransportMode.LOCAL
        )
        event = await sync_to_async(Event.new)(EventAction.LOGIN)
        event.set_user(self.user)
        await event.asave()
        notification = Notification(
            user=self.user,
            body="foo",
            event=event,
            hyperlink="goauthentik.io",
            hyperlink_label="a link",
        )
        await sync_to_async(transport.send_local)(notification)

        evt = await communicator.receive_json_from(timeout=5)
        self.assertEqual(evt["message_type"], "notification.new")
        self.assertEqual(evt["id"], str(notification.pk))
        self.assertEqual(evt["data"]["pk"], str(notification.pk))
        self.assertEqual(evt["data"]["body"], "foo")
        self.assertEqual(evt["data"]["event"]["pk"], str(event.pk))

        await communicator.disconnect()
