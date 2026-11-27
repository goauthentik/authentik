"""Test http utils"""

from decimal import Decimal

from django.test import TestCase
from requests.exceptions import JSONDecodeError

from authentik.lib.config import CONFIG
from authentik.lib.utils.http import (
    DebugSession,
    MsgspecHTTPAdapter,
    MsgspecResponse,
    get_http_session,
)


def response(content: bytes) -> MsgspecResponse:
    """Build a response with the given body"""
    resp = MsgspecResponse()
    resp.status_code = 200
    resp.encoding = "utf-8"
    resp._content = content
    return resp


class TestHTTPUtils(TestCase):
    """Test http-utils"""

    def test_json(self):
        """Test JSON decoding via msgspec"""
        self.assertEqual(response(b'{"foo": "bar"}').json(), {"foo": "bar"})
        self.assertEqual(response(b"[1, 2, 3]").json(), [1, 2, 3])

    def test_json_invalid(self):
        """Test invalid JSON body"""
        with self.assertRaises(JSONDecodeError):
            response(b"{not json").json()

    def test_json_empty(self):
        """Test empty body"""
        with self.assertRaises(JSONDecodeError):
            response(b"").json()

    def test_json_kwargs(self):
        """Test that json.loads kwargs fall back to the default decoder"""
        self.assertEqual(
            response(b'{"foo": 1.5}').json(parse_float=Decimal),
            {"foo": Decimal("1.5")},
        )

    def test_session_adapters(self):
        """Test that sessions from get_http_session use the msgspec adapter"""
        session = get_http_session()
        self.assertIsInstance(session.get_adapter("https://goauthentik.io"), MsgspecHTTPAdapter)
        self.assertIsInstance(session.get_adapter("http://goauthentik.io"), MsgspecHTTPAdapter)

    @CONFIG.patch("log_level", "trace")
    def test_session_adapters_debug(self):
        """Test that the debug session also uses the msgspec adapter"""
        session = get_http_session()
        self.assertIsInstance(session, DebugSession)
        self.assertIsInstance(session.get_adapter("https://goauthentik.io"), MsgspecHTTPAdapter)
        self.assertIsInstance(session.get_adapter("http://goauthentik.io"), MsgspecHTTPAdapter)
