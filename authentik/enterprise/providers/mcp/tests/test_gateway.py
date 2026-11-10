"""MCP gateway tests"""

import json
from dataclasses import asdict

from django.urls import reverse
from django.utils import timezone
from jwt import decode
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.enterprise.providers.mcp.client import decode_header_value, encode_header_value
from authentik.enterprise.providers.mcp.models import MCPBackend, MCPGatewayProvider
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider

MODERN = "2026-07-28"
PV = "io.modelcontextprotocol/protocolVersion"


def oauth2_app() -> tuple[Application, OAuth2Provider]:
    provider = OAuth2Provider.objects.create(
        name=generate_id(), authorization_flow=create_test_flow()
    )
    app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
    return app, provider


class FakeBackend:
    """Fake MCP server. Legacy backends require a session from `initialize`, modern ones
    validate the mirrored headers. `tools/call` echoes its params."""

    def __init__(self, mock: Mocker, tools: list[dict], modern=False, sse=False):
        self.url = f"https://{generate_id()}.example.com/mcp"
        self.tools = tools
        self.modern = modern
        self.sse = sse
        self.sessions: set[str] = set()
        self.methods: list[str] = []
        mock.post(self.url, text=self.respond)
        mock.delete(self.url, text=self.delete)

    def delete(self, request, context):
        self.sessions.discard(request.headers.get("Mcp-Session-Id"))
        return ""

    def reply(self, context, message_id, result=None, error=None, status=200):
        context.status_code = status
        body = {"jsonrpc": "2.0", "id": message_id}
        body.update({"error": error} if error else {"result": result})
        body = json.dumps(body)
        if self.sse:
            context.headers["Content-Type"] = "text/event-stream"
            # A notification before the response, which must be skipped
            note = json.dumps({"jsonrpc": "2.0", "method": "notifications/progress"})
            return f"data: {note}\n\ndata: {body}\n\n"
        context.headers["Content-Type"] = "application/json"
        return body

    def respond(self, request, context):
        message = request.json()
        method = message.get("method")
        self.methods.append(method)
        if "id" not in message:
            context.status_code = 202
            return ""
        params = message.get("params") or {}
        if self.modern:
            return self.respond_modern(request, context, message, params)
        if method == "initialize":
            session = generate_id()
            self.sessions.add(session)
            context.headers["Mcp-Session-Id"] = session
            return self.reply(context, message["id"], {"protocolVersion": "2025-11-25"})
        session = request.headers.get("Mcp-Session-Id")
        if not session:
            error = {"code": -32000, "message": "Bad Request: No valid session ID provided"}
            return self.reply(context, message["id"], error=error, status=400)
        if session not in self.sessions:
            context.status_code = 404
            return ""
        return self.reply(context, message["id"], self.result(method, params))

    def respond_modern(self, request, context, message, params):
        method = message["method"]
        headers = request.headers
        mismatch = headers.get("Mcp-Method") != method or (
            headers.get("MCP-Protocol-Version") != (params.get("_meta") or {}).get(PV)
        )
        if method == "tools/call":
            mismatch |= decode_header_value(headers.get("Mcp-Name", "")) != params["name"]
            region = (params.get("arguments") or {}).get("region")
            if region is not None:
                mismatch |= headers.get("Mcp-Param-Region") != region
        if mismatch:
            error = {"code": -32020, "message": "Header mismatch"}
            return self.reply(context, message["id"], error=error, status=400)
        if method == "server/discover":
            return self.reply(
                context, message["id"], {"supportedVersions": [MODERN], "capabilities": {}}
            )
        return self.reply(context, message["id"], self.result(method, params))

    def result(self, method: str, params: dict) -> dict:
        if method == "tools/list":
            return {"tools": self.tools}
        if method == "tools/call":
            params = {key: value for key, value in params.items() if key != "_meta"}
            return {"content": [{"type": "text", "text": json.dumps(params)}]}
        return {}


def tool(name: str, schema: dict | None = None) -> dict:
    return {"name": name, "inputSchema": schema or {"type": "object"}}


class MCPGatewayTestCase(APITestCase):
    def setUp(self):
        self.app, self.provider = oauth2_app()
        self.gateway = MCPGatewayProvider.objects.create(
            name=generate_id(), backchannel_application=self.app
        )
        self.user = create_test_user()
        self.token = self.create_token(self.user)
        self.url = reverse(
            "authentik_providers_mcp:gateway", kwargs={"application_slug": self.app.slug}
        )

    def create_token(self, user) -> AccessToken:
        return AccessToken.objects.create(
            provider=self.provider,
            user=user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid profile",
            _id_token=json.dumps(asdict(IDToken("foo", "bar"))),
        )

    def add_backend(self, backend: FakeBackend, slug="docs") -> MCPBackend:
        return MCPBackend.objects.create(
            gateway=self.gateway, name=slug, slug=slug, url=backend.url
        )

    def rpc(self, method: str, params: dict | None = None, token=None, **headers):
        return self.client.post(
            self.url,
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {token or self.token.token}",
            headers=headers,
        )

    def modern_rpc(self, method: str, params: dict | None = None, version=MODERN, **headers):
        params = {**(params or {}), "_meta": {PV: version}}
        headers = {"MCP-Protocol-Version": version, "Mcp-Method": method, **headers}
        return self.rpc(method, params, **headers)


class TestMCPGateway(MCPGatewayTestCase):
    def test_unauthorized(self):
        res = self.rpc("initialize", token=generate_id())
        self.assertEqual(res.status_code, 401)
        self.assertIn("resource_metadata=", res["WWW-Authenticate"])

    def test_token_other_provider(self):
        """Tokens of other OAuth2 providers are rejected"""
        _, other = oauth2_app()
        self.token.provider = other
        self.token.save()
        self.assertEqual(self.rpc("initialize").status_code, 401)

    def test_protected_resource_metadata(self):
        res = self.client.get(
            reverse(
                "authentik_providers_mcp:protected-resource-metadata",
                kwargs={"application_slug": self.app.slug},
            )
        )
        body = res.json()
        self.assertEqual(body["resource"], f"http://testserver{self.url}")
        self.assertEqual(
            body["authorization_servers"], [f"http://testserver/application/o/{self.app.slug}/"]
        )

    def test_initialize(self):
        res = self.rpc("initialize", {"protocolVersion": "2025-06-18"})
        self.assertEqual(res.json()["result"]["protocolVersion"], "2025-06-18")
        self.assertIn("Mcp-Session-Id", res)
        res = self.rpc("unknown")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["error"]["code"], -32601)

    @Mocker()
    def test_list_tools(self, mock: Mocker):
        self.add_backend(FakeBackend(mock, [tool("search"), tool("delete")], sse=True))
        policy = ExpressionPolicy.objects.create(
            name=generate_id(), expression='return context["mcp"]["tool"] != "delete"'
        )
        PolicyBinding.objects.create(target=self.gateway.backends.first(), policy=policy, order=0)
        res = self.rpc("tools/list")
        names = [tool["name"] for tool in res.json()["result"]["tools"]]
        self.assertEqual(names, ["docs__search"])

    @Mocker()
    def test_call_tool(self, mock: Mocker):
        backend = FakeBackend(mock, [tool("search")])
        self.add_backend(backend)
        res = self.rpc("tools/call", {"name": "docs__search", "arguments": {"q": "foo"}})
        text = res.json()["result"]["content"][0]["text"]
        self.assertEqual(json.loads(text), {"name": "search", "arguments": {"q": "foo"}})
        # Without a gateway session, the backend session only lives for the call
        self.assertEqual(backend.sessions, set())
        event = Event.objects.get(action=EventAction.MCP_TOOL_CALL)
        self.assertTrue(event.context["passing"])
        self.assertEqual(event.context["tool"], "search")

    @Mocker()
    def test_call_tool_denied(self, mock: Mocker):
        backend = self.add_backend(FakeBackend(mock, [tool("delete")]))
        policy = ExpressionPolicy.objects.create(
            name=generate_id(), expression='return context["mcp"]["arguments"].get("force") != True'
        )
        PolicyBinding.objects.create(target=backend, policy=policy, order=0)
        res = self.rpc("tools/call", {"name": "docs__delete", "arguments": {"force": True}})
        self.assertTrue(res.json()["result"]["isError"])
        self.assertFalse(mock.called)
        event = Event.objects.get(action=EventAction.MCP_TOOL_CALL)
        self.assertFalse(event.context["passing"])

    def test_call_unknown_tool(self):
        res = self.rpc("tools/call", {"name": "nope__search"})
        self.assertEqual(res.json()["error"]["code"], -32602)

    @Mocker()
    def test_linked_application_token(self, mock: Mocker):
        """Backends with a linked application receive a token issued by its provider"""
        linked_app, linked_provider = oauth2_app()
        backend = self.add_backend(FakeBackend(mock, [tool("search")]))
        backend.token_application = linked_app
        backend.save()
        self.rpc("tools/call", {"name": "docs__search"})
        raw = mock.last_request.headers["Authorization"].removeprefix("Bearer ")
        issued = AccessToken.objects.get(token=raw)
        self.assertEqual(issued.provider, linked_provider)
        self.assertEqual(issued.user, self.user)
        claims = decode(raw, options={"verify_signature": False})
        self.assertEqual(claims["aud"], linked_provider.client_id)

    @Mocker()
    def test_linked_application_denied(self, mock: Mocker):
        """Users without access to the linked application can't see its tools"""
        linked_app, _ = oauth2_app()
        PolicyBinding.objects.create(target=linked_app, user=create_test_user(), order=0)
        backend = self.add_backend(FakeBackend(mock, [tool("search")]))
        backend.token_application = linked_app
        backend.save()
        self.assertEqual(self.rpc("tools/list").json()["result"]["tools"], [])
        res = self.rpc("tools/call", {"name": "docs__search"})
        self.assertTrue(res.json()["result"]["isError"])


class TestMCPGatewaySessions(MCPGatewayTestCase):
    """Legacy clients get a gateway session carrying the backends' sessions"""

    @Mocker()
    def test_session_reuse(self, mock: Mocker):
        backend = FakeBackend(mock, [tool("search")])
        self.add_backend(backend)
        session = self.rpc("initialize")["Mcp-Session-Id"]
        self.assertEqual(len(backend.sessions), 1)
        for _ in range(2):
            res = self.rpc("tools/call", {"name": "docs__search"}, **{"Mcp-Session-Id": session})
            self.assertNotIn("isError", res.json()["result"])
        self.assertEqual(backend.methods.count("initialize"), 1)
        # The backend's session stays open until the client terminates the gateway session
        self.assertEqual(len(backend.sessions), 1)
        res = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
            headers={"Mcp-Session-Id": session},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(backend.sessions, set())

    @Mocker()
    def test_session_invalid(self, mock: Mocker):
        self.add_backend(FakeBackend(mock, [tool("search")]))
        session = self.rpc("initialize")["Mcp-Session-Id"]
        res = self.rpc("tools/list", **{"Mcp-Session-Id": generate_id()})
        self.assertEqual(res.status_code, 404)
        # Sessions are bound to their user
        other = self.create_token(create_test_user())
        res = self.rpc("tools/list", token=other.token, **{"Mcp-Session-Id": session})
        self.assertEqual(res.status_code, 404)

    @Mocker()
    def test_session_expired_backend(self, mock: Mocker):
        """When a backend drops its session, calls continue with a new one"""
        backend = FakeBackend(mock, [tool("search")])
        self.add_backend(backend)
        session = self.rpc("initialize")["Mcp-Session-Id"]
        backend.sessions.clear()
        res = self.rpc("tools/call", {"name": "docs__search"}, **{"Mcp-Session-Id": session})
        self.assertNotIn("isError", res.json()["result"])
        self.assertEqual(backend.methods.count("initialize"), 2)


class TestMCPGatewayModern(MCPGatewayTestCase):
    """2026-07-28 clients and backends"""

    def test_discover(self):
        res = self.modern_rpc("server/discover")
        result = res.json()["result"]
        self.assertEqual(result["supportedVersions"][0], MODERN)
        self.assertIn("2025-11-25", result["supportedVersions"])
        self.assertEqual(result["resultType"], "complete")
        self.assertNotIn("Mcp-Session-Id", res)

    def test_header_mismatch(self):
        res = self.modern_rpc("ping", **{"Mcp-Method": "tools/list"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], -32020)
        res = self.modern_rpc("tools/call", {"name": "docs__search"}, **{"Mcp-Name": "other"})
        self.assertEqual(res.json()["error"]["code"], -32020)

    def test_unsupported_version(self):
        res = self.modern_rpc("ping", version="1900-01-01")
        self.assertEqual(res.status_code, 400)
        error = res.json()["error"]
        self.assertEqual(error["code"], -32022)
        self.assertEqual(error["data"]["requested"], "1900-01-01")
        self.assertIn(MODERN, error["data"]["supported"])

    def test_unknown_method(self):
        res = self.modern_rpc("unknown")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["error"]["code"], -32601)

    @Mocker()
    def test_call_tool_base64_name(self, mock: Mocker):
        self.add_backend(FakeBackend(mock, [tool("suche-ü")]))
        name = "docs__suche-ü"
        res = self.modern_rpc(
            "tools/call", {"name": name}, **{"Mcp-Name": encode_header_value(name)}
        )
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("isError", res.json()["result"])

    @Mocker()
    def test_modern_backend(self, mock: Mocker):
        backend = FakeBackend(mock, [tool("search")], modern=True)
        self.add_backend(backend)
        for _ in range(2):
            res = self.rpc("tools/call", {"name": "docs__search"})
            self.assertNotIn("isError", res.json()["result"])
        # The era is detected once, and no handshake is needed
        self.assertEqual(backend.methods, ["server/discover", "tools/call", "tools/call"])
        self.assertEqual(mock.last_request.json()["params"]["_meta"][PV], MODERN)

    @Mocker()
    def test_modern_backend_param_headers(self, mock: Mocker):
        """Parameters mirrored into headers are hidden from the client, and added by the
        gateway after the backend reports a header mismatch"""
        schema = {
            "type": "object",
            "properties": {"region": {"type": "string", "x-mcp-header": "Region"}},
        }
        backend = FakeBackend(mock, [tool("query", schema)], modern=True)
        self.add_backend(backend)
        listed = self.rpc("tools/list").json()["result"]["tools"][0]
        self.assertNotIn("x-mcp-header", listed["inputSchema"]["properties"]["region"])
        res = self.rpc("tools/call", {"name": "docs__query", "arguments": {"region": "eu 1"}})
        self.assertNotIn("isError", res.json()["result"])
        self.assertEqual(mock.last_request.headers["Mcp-Param-Region"], "eu 1")

    def test_header_value_encoding(self):
        for value, encoded in [
            ("us-west1", "us-west1"),
            ("Hello, 世界", "=?base64?SGVsbG8sIOS4lueVjA==?="),
            (" padded ", "=?base64?IHBhZGRlZCA=?="),
            ("=?base64?literal?=", "=?base64?PT9iYXNlNjQ/bGl0ZXJhbD89?="),
        ]:
            self.assertEqual(encode_header_value(value), encoded)
            self.assertEqual(decode_header_value(encoded), value)
        self.assertEqual(encode_header_value(True), "true")
