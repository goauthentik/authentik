from unittest.mock import patch

from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.http import HttpRequest
from django.test import TransactionTestCase

from authentik.core.tests.utils import create_test_user
from authentik.events.models import (
    Event,
    EventAction,
    Notification,
    NotificationTransport,
    TransportMode,
)
from authentik.flows.apps import RefreshOtherFlowsAfterAuthentication
from authentik.lib.generators import generate_id
from authentik.root import websocket
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.user_login.stage import COOKIE_NAME_KNOWN_DEVICE
from authentik.tenants.utils import get_current_tenant


class TestClientWS(TransactionTestCase):

    def setUp(self):
        tenant = get_current_tenant()
        tenant.flags[RefreshOtherFlowsAfterAuthentication().key] = True
        tenant.save()
        self.user = create_test_user()

    async def _alogin_cookie(self, user, **kwargs):
        """Similar to `client.aforce_login` but allow setting of cookies"""
        from django.contrib.auth import alogin

        # Create a fake request to store login details.
        request = HttpRequest()
        session = await self.client.asession()
        request.session = session
        request.COOKIES.update(kwargs)

        await alogin(request, user, BACKEND_INBUILT)
        # Save the session values.
        await request.session.asave()
        self.client._set_login_cookies(request)

    async def test_auth_blank(self):
        dev_id = generate_id()
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            "/ws/client/",
            headers=[(b"cookie", f"{COOKIE_NAME_KNOWN_DEVICE}={dev_id}".encode())],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await self._alogin_cookie(self.user, **{COOKIE_NAME_KNOWN_DEVICE: dev_id})

        await communicator.receive_nothing()
        await communicator.receive_json_from()
        await communicator.disconnect()

    async def test_tab_refresh(self):
        dev_id = generate_id()
        communicator = WebsocketCommunicator(
            URLRouter(websocket.websocket_urlpatterns),
            "/ws/client/",
            headers=[(b"cookie", f"{COOKIE_NAME_KNOWN_DEVICE}={dev_id}".encode())],
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        with patch("authentik.flows.apps.RefreshOtherFlowsAfterAuthentication.get") as flag:
            flag.return_value = True
            await self._alogin_cookie(self.user, **{COOKIE_NAME_KNOWN_DEVICE: dev_id})

        evt = await communicator.receive_json_from()
        self.assertEqual(
            evt, {"message_type": "session.authenticated", "type": "event.session.authenticated"}
        )

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
