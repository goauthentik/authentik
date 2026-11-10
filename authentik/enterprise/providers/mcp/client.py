"""Minimal MCP Streamable HTTP client, used to talk to backend MCP servers.

Speaks both protocol eras: the stateless 2026-07-28 revision (per-request `_meta` and
headers), and earlier revisions with an `initialize` handshake and optional sessions."""

from base64 import b64decode, b64encode
from dataclasses import dataclass
from hashlib import sha256
from http import HTTPStatus
from json import JSONDecodeError, loads
from typing import Any, Self

from django.core.cache import cache
from mcp_types import (
    CLIENT_CAPABILITIES_META_KEY,
    CLIENT_INFO_META_KEY,
    PROTOCOL_VERSION_META_KEY,
    Implementation,
    InitializeRequestParams,
)
from mcp_types.jsonrpc import (
    HEADER_MISMATCH,
    JSONRPC_VERSION,
    METHOD_NOT_FOUND,
    MISSING_REQUIRED_CLIENT_CAPABILITY,
    UNSUPPORTED_PROTOCOL_VERSION,
    JSONRPCNotification,
    JSONRPCRequest,
)
from mcp_types.version import LATEST_HANDSHAKE_VERSION, MODERN_PROTOCOL_VERSIONS
from pydantic import BaseModel
from requests import RequestException, Response

from authentik import authentik_version
from authentik.lib.generators import generate_id
from authentik.lib.utils.http import get_http_session

HEADER_SESSION_ID = "Mcp-Session-Id"
HEADER_PROTOCOL_VERSION = "MCP-Protocol-Version"
HEADER_METHOD = "Mcp-Method"
HEADER_NAME = "Mcp-Name"
HEADER_PARAM_PREFIX = "Mcp-Param-"
# Methods whose `params.name` (or `params.uri`) is mirrored into `Mcp-Name`
NAMED_METHODS = {"tools/call": "name", "prompts/get": "name", "resources/read": "uri"}

# Characters allowed in plain header values
PRINTABLE_ASCII = range(0x20, 0x7F)
BASE64_PREFIX = "=?base64?"
BASE64_SUFFIX = "?="

# Detected era of a backend, cached per URL as the spec recommends
CACHE_KEY_ERA = "goauthentik.io/providers/mcp/era/%s"
CACHE_TIMEOUT_ERA = 60 * 60
ERA_LEGACY = "legacy"

MODERN_ERRORS = {HEADER_MISMATCH, MISSING_REQUIRED_CLIENT_CAPABILITY, UNSUPPORTED_PROTOCOL_VERSION}


class MCPClientError(Exception):
    """Backend MCP server failed or returned a JSON-RPC error"""

    def __init__(
        self, message: str, code: int | None = None, status: int | None = None, data: Any = None
    ):
        super().__init__(message)
        self.code = code
        self.status = status
        self.data = data

    @property
    def is_modern(self) -> bool:
        """Whether this error identifies a 2026-07-28+ server"""
        return self.code in MODERN_ERRORS or (
            self.status == HTTPStatus.NOT_FOUND and self.code == METHOD_NOT_FOUND
        )


@dataclass(slots=True)
class BackendSession:
    """Negotiated protocol version, and for legacy servers the session ID"""

    version: str
    session_id: str | None = None

    @property
    def is_modern(self) -> bool:
        return self.version in MODERN_PROTOCOL_VERSIONS


def encode_header_value(value: str | int | bool) -> str:
    """Encode a value for `Mcp-Name` or `Mcp-Param-*`, using the base64 sentinel for values
    which aren't safe as plain header values"""
    if isinstance(value, bool):
        value = "true" if value else "false"
    value = str(value)
    safe = (
        all(ord(char) in PRINTABLE_ASCII for char in value)
        and value == value.strip()
        and not (value.startswith(BASE64_PREFIX) and value.endswith(BASE64_SUFFIX))
    )
    if safe:
        return value
    return f"{BASE64_PREFIX}{b64encode(value.encode()).decode()}{BASE64_SUFFIX}"


def decode_header_value(value: str) -> str:
    if value.startswith(BASE64_PREFIX) and value.endswith(BASE64_SUFFIX):
        return b64decode(value.removeprefix(BASE64_PREFIX).removesuffix(BASE64_SUFFIX)).decode()
    return value


def param_headers(schema: dict[str, Any], arguments: dict[str, Any]) -> dict[str, str]:
    """`Mcp-Param-*` headers for tool parameters annotated with `x-mcp-header`.
    Annotations are only valid on properties reachable through `properties` chains."""
    # ponytail: tools with invalid annotations aren't excluded from tools/list as the spec
    # requires, the backend rejects calls to them instead
    headers = {}

    def walk(properties: dict[str, Any], values: Any):
        for key, prop in (properties or {}).items():
            value = values.get(key) if isinstance(values, dict) else None
            if (name := prop.get("x-mcp-header")) and value is not None:
                headers[f"{HEADER_PARAM_PREFIX}{name}"] = encode_header_value(value)
            walk(prop.get("properties"), value)

    walk(schema.get("properties"), arguments)
    return headers


def strip_param_headers(schema: dict[str, Any]) -> dict[str, Any]:
    """Remove `x-mcp-header` annotations from a tool's input schema"""
    schema = {key: value for key, value in schema.items() if key != "x-mcp-header"}
    if isinstance(schema.get("properties"), dict):
        schema["properties"] = {
            key: strip_param_headers(prop) if isinstance(prop, dict) else prop
            for key, prop in schema["properties"].items()
        }
    return schema


class MCPClient:
    """Connection to a backend MCP server.

    Used as a context manager for a single exchange, which negotiates the protocol (unless
    resuming `session`) on enter, and terminates any session it created on exit."""

    def __init__(self, url: str, token: str | None = None, session: BackendSession | None = None):
        self.url = url
        self.session = session
        self._owns_session = False
        self.http = get_http_session()
        # TEMP: trust akbench's self-signed certificate, revert before committing
        self.http.verify = False
        self.http.headers["Accept"] = "application/json, text/event-stream"
        if token:
            self.http.headers["Authorization"] = f"Bearer {token}"

    def __enter__(self) -> Self:
        if not self.session:
            self.session = self.open()
            self._owns_session = True
        return self

    def __exit__(self, *_):
        if self._owns_session:
            self.terminate()
        self.http.close()

    @property
    def _era_cache_key(self) -> str:
        return CACHE_KEY_ERA % sha256(self.url.encode()).hexdigest()

    def open(self) -> BackendSession:
        """Detect the server's era and negotiate a protocol version. Sessions opened by this
        aren't terminated automatically."""
        era = cache.get(self._era_cache_key)
        if era in MODERN_PROTOCOL_VERSIONS:
            return BackendSession(era)
        if era != ERA_LEGACY:
            if version := self._discover():
                cache.set(self._era_cache_key, version, CACHE_TIMEOUT_ERA)
                return BackendSession(version)
            cache.set(self._era_cache_key, ERA_LEGACY, CACHE_TIMEOUT_ERA)
        return self._initialize()

    def _discover(self) -> str | None:
        """Probe with `server/discover`, returning the modern version to use if any"""
        self.session = BackendSession(MODERN_PROTOCOL_VERSIONS[-1])
        try:
            supported = self.request("server/discover").get("supportedVersions", [])
        except MCPClientError as exc:
            if not exc.is_modern:
                return None
            supported = (exc.data or {}).get("supported", []) if isinstance(exc.data, dict) else []
            # A modern server without discovery
            if exc.code == METHOD_NOT_FOUND:
                supported = [self.session.version]
        finally:
            self.session = None
        return next((v for v in reversed(MODERN_PROTOCOL_VERSIONS) if v in supported), None)

    def _initialize(self) -> BackendSession:
        result = self.request(
            "initialize",
            InitializeRequestParams(
                protocol_version=LATEST_HANDSHAKE_VERSION,
                capabilities={},
                client_info=self._client_info(),
            ).model_dump(by_alias=True, exclude_none=True),
        )
        # `request` stores the session ID the server assigned
        session_id = self.session.session_id if self.session else None
        self.session = BackendSession(
            result.get("protocolVersion", LATEST_HANDSHAKE_VERSION), session_id
        )
        self._post(
            JSONRPCNotification(jsonrpc=JSONRPC_VERSION, method="notifications/initialized")
        ).close()
        return self.session

    def terminate(self):
        """Terminate the legacy session, if any"""
        if not self.session or not self.session.session_id:
            return
        try:
            self.http.delete(self.url, headers=self._headers())
        except RequestException:
            pass

    @staticmethod
    def _client_info() -> Implementation:
        return Implementation(name="authentik", version=authentik_version())

    def _headers(self) -> dict[str, str]:
        if not self.session:
            return {}
        headers = {HEADER_PROTOCOL_VERSION: self.session.version}
        if self.session.session_id:
            headers[HEADER_SESSION_ID] = self.session.session_id
        return headers

    def _post(self, message: BaseModel, headers: dict[str, str] | None = None) -> Response:
        try:
            response = self.http.post(
                self.url,
                json=message.model_dump(by_alias=True, exclude_none=True),
                headers={**self._headers(), **(headers or {})},
                stream=True,
            )
        except RequestException as exc:
            raise MCPClientError(str(exc)) from exc
        if session_id := response.headers.get(HEADER_SESSION_ID):
            self.session = BackendSession(
                self.session.version if self.session else LATEST_HANDSHAKE_VERSION, session_id
            )
        return response

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a JSON-RPC request and return its result"""
        try:
            return self._request(method, params, headers)
        except MCPClientError as exc:
            resumed = self.session and self.session.session_id and not self._owns_session
            if exc.status != HTTPStatus.NOT_FOUND or not resumed:
                raise
        # The server dropped the resumed legacy session, so use a new one for this exchange
        # ponytail: the client's gateway session keeps the stale ID, so every following
        # exchange pays for a handshake until the client re-initializes
        self.session = None
        self.session = self._initialize()
        self._owns_session = True
        return self._request(method, params, headers)

    def _request(
        self,
        method: str,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> dict[str, Any]:
        params = dict(params or {})
        headers = dict(headers or {})
        if self.session and self.session.is_modern:
            params["_meta"] = {
                **params.get("_meta", {}),
                PROTOCOL_VERSION_META_KEY: self.session.version,
                CLIENT_INFO_META_KEY: self._client_info().model_dump(exclude_none=True),
                CLIENT_CAPABILITIES_META_KEY: {},
            }
            headers[HEADER_METHOD] = method
            if (field := NAMED_METHODS.get(method)) and field in params:
                headers[HEADER_NAME] = encode_header_value(params[field])

        message_id = generate_id()
        message = JSONRPCRequest(
            jsonrpc=JSONRPC_VERSION, id=message_id, method=method, params=params
        )
        with self._post(message, headers) as response:
            reply = self._read_reply(response, message_id)
        # Servers answer auth failures before reaching JSON-RPC, e.g. {"error": "..."}
        if isinstance(error := reply.get("error"), str):
            raise MCPClientError(error, status=response.status_code)
        if error:
            raise MCPClientError(
                error.get("message", "unknown error"),
                code=error.get("code"),
                status=response.status_code,
                data=error.get("data"),
            )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise MCPClientError(f"HTTP {response.status_code}", status=response.status_code)
        return reply.get("result", {})

    def _read_reply(self, response: Response, message_id: str) -> dict[str, Any]:
        if response.headers.get("Content-Type", "").startswith("text/event-stream"):
            return self._read_sse(response, message_id)
        try:
            reply = loads(response.content)
        except JSONDecodeError, UnicodeDecodeError:
            reply = None
        return reply if isinstance(reply, dict) else {}

    @staticmethod
    def _read_sse(response: Response, message_id: str) -> dict[str, Any]:
        """Read SSE events until the response to `message_id` arrives, skipping any
        notifications or requests the server sends first"""
        data: list[str] = []
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data:"):
                data.append(line.removeprefix("data:").strip())
                continue
            if line or not data:
                continue
            # A blank line dispatches the event
            message = loads("\n".join(data))
            data = []
            if message.get("id") == message_id:
                return message
        raise MCPClientError("Stream ended without a response")

    def list_tools(self) -> list[dict[str, Any]]:
        """List all tools, following pagination"""
        tools, cursor = [], None
        while True:
            result = self.request("tools/list", {"cursor": cursor} if cursor else {})
            tools.extend(result.get("tools", []))
            cursor = result.get("nextCursor")
            if not cursor:
                return tools

    def call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        """Call a tool. On modern servers, a header mismatch means the tool mirrors
        parameters into headers, so look up its schema and retry with them."""
        try:
            return self.request("tools/call", params)
        except MCPClientError as exc:
            if exc.code != HEADER_MISMATCH:
                raise
        tool = next((t for t in self.list_tools() if t.get("name") == params.get("name")), None)
        if not tool:
            raise MCPClientError(f"Unknown tool {params.get('name')}")
        headers = param_headers(tool.get("inputSchema", {}), params.get("arguments") or {})
        return self.request("tools/call", params, headers)
