"""Tests for the internal WebSocket endpoints the Rust server calls"""

import zlib
from json import dumps
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django_channels_postgres.layer import PostgresChannelLayerLoopProxy
from structlog.testing import capture_logs

from authentik.core.tests.utils import create_test_session, create_test_user
from authentik.events.consumer import build_user_group

# Shared with the Rust tests in `src/server/websocket/codec.rs`, which decode the bytes the
# Python channel layer produced for this message.
PYTHON_NOTIFICATION_MESSAGE = {
    "type": "event.notification",
    "id": "5ba8d8bc-5d36-4a17-9bba-e1b8c3d6a0b4",
    "data": {
        "pk": "5ba8d8bc-5d36-4a17-9bba-e1b8c3d6a0b4",
        "severity": "notice",
        "body": "Ünïcödé body",
        "created": "2026-11-12T10:00:00.000000Z",
        "event": None,
        "seen": False,
        "hyperlink": None,
        "hyperlink_label": None,
        "count": 3,
        "ratio": 0.5,
        "tags": ["a", "b"],
    },
}
PYTHON_NOTIFICATION_FIXTURE = (
    Path(__file__).parents[3] / "src/server/websocket/testdata/notification.msgpack.zlib"
)


class TestWebsocketAuthorize(TestCase):
    """Tests for `WebsocketAuthorizeView`"""

    def setUp(self):
        self.user = create_test_user()
        self.url = reverse("internal-ws-authorize")

    def authorize(self, headers: dict[str, str] | None = None, route: str = "client"):
        return self.client.post(
            self.url,
            data=dumps({"route": route, "path": "/ws/client/", "headers": headers or {}}),
            content_type="application/json",
        )

    def test_unauthenticated(self):
        """Handshakes without a session are denied, like `ClientConsumer.connect`"""
        response = self.authorize()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"accept": False, "groups": []})

    def test_authenticated(self):
        """A logged-in session joins the user's notification group"""
        session = create_test_session(self.user)
        response = self.authorize(
            {"cookie": f"{settings.SESSION_COOKIE_NAME}={session.session.session_key}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"accept": True, "groups": [build_user_group(self.user)]})

    def test_unknown_session(self):
        """A session cookie for a session that doesn't exist is denied"""
        response = self.authorize({"cookie": f"{settings.SESSION_COOKIE_NAME}=foo"})
        self.assertEqual(response.json(), {"accept": False, "groups": []})

    def test_malformed_cookie(self):
        """A cookie header that doesn't parse is denied, not an error"""
        response = self.authorize({"cookie": '=;;garbage; "unterminated; a=b=c'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["accept"])

    def test_logs_connection(self):
        """The connection is logged like `ChannelsLoggingMiddleware` logs it"""
        with capture_logs() as logs:
            self.authorize(
                {"user-agent": "Mozilla/5.0 Meta\\xa0AI", "x-forwarded-for": "\\xff"},
            )
        log = next(log for log in logs if log.get("scheme") == "ws")
        self.assertEqual(log["event"], "/ws/client/")
        self.assertEqual(log["user_agent"], "Mozilla/5.0 Meta\\xa0AI")
        self.assertEqual(log["remote"], "\\xff")
        self.assertFalse(log["accepted"])

    def test_unknown_route(self):
        """Routes without an authorizer are rejected"""
        self.assertEqual(self.authorize(route="outpost").status_code, 400)

    def test_malformed_body(self):
        """A body that isn't JSON is rejected"""
        response = self.client.post(self.url, data=b"\xff", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_only_post(self):
        """The endpoint only accepts POST"""
        self.assertEqual(self.client.get(self.url).status_code, 405)


class TestChannelLayerFixture(TestCase):
    """The Rust server decodes channel layer messages itself"""

    def test_serialization_matches_rust_fixture(self):
        """The Python channel layer still serializes messages like the fixture the Rust tests
        decode. If this fails, update the fixture and the Rust decoder together."""
        layer = PostgresChannelLayerLoopProxy()
        fixture = PYTHON_NOTIFICATION_FIXTURE.read_bytes()
        self.assertEqual(
            zlib.decompress(layer.serialize(PYTHON_NOTIFICATION_MESSAGE)),
            zlib.decompress(fixture),
        )
        self.assertEqual(layer.deserialize(fixture), PYTHON_NOTIFICATION_MESSAGE)
