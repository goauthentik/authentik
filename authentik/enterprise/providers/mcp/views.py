"""MCP gateway views"""

from http import HTTPStatus
from typing import Any

from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from mcp_types import (
    PROTOCOL_VERSION_META_KEY,
    SERVER_INFO_META_KEY,
    CallToolRequestParams,
    CallToolResult,
    DiscoverResult,
    Implementation,
    InitializeResult,
    ServerCapabilities,
    TextContent,
    ToolsCapability,
)
from mcp_types.jsonrpc import (
    HEADER_MISMATCH,
    INVALID_PARAMS,
    INVALID_REQUEST,
    JSONRPC_VERSION,
    METHOD_NOT_FOUND,
    UNSUPPORTED_PROTOCOL_VERSION,
    ErrorData,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    jsonrpc_message_adapter,
)
from mcp_types.version import (
    HANDSHAKE_PROTOCOL_VERSIONS,
    LATEST_HANDSHAKE_VERSION,
    MODERN_PROTOCOL_VERSIONS,
)
from pydantic import BaseModel, ValidationError
from structlog.stdlib import get_logger

from authentik import authentik_version
from authentik.api.authentication import validate_auth
from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import Application
from authentik.enterprise.providers.mcp.client import (
    HEADER_METHOD,
    HEADER_NAME,
    HEADER_PROTOCOL_VERSION,
    HEADER_SESSION_ID,
    NAMED_METHODS,
    BackendSession,
    MCPClient,
    MCPClientError,
    decode_header_value,
    strip_param_headers,
)
from authentik.enterprise.providers.mcp.models import TOOL_SEPARATOR, MCPBackend, MCPGatewayProvider
from authentik.enterprise.providers.mcp.sessions import decode_session, encode_session
from authentik.events.models import Event, EventAction
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.engine import PolicyEngine
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider

LOGGER = get_logger()

SUPPORTED_VERSIONS = [*reversed(MODERN_PROTOCOL_VERSIONS), *reversed(HANDSHAKE_PROTOCOL_VERSIONS)]


class RPCError(Exception):
    def __init__(self, code: int, message: str, status: int = 200, data: Any = None):
        super().__init__(message)
        self.status = status
        self.error = ErrorData(code=code, message=message)
        if data is not None:
            self.error.data = data


def dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json", by_alias=True, exclude_none=True)


def gateway_provider(application_slug: str) -> tuple[MCPGatewayProvider, OAuth2Provider]:
    """Get the gateway for an application, and the OAuth2 provider which issues its tokens"""
    gateway = get_object_or_404(
        MCPGatewayProvider.objects.select_related("backchannel_application"),
        backchannel_application__slug=application_slug,
    )
    provider = gateway.backchannel_application.get_provider()
    if not isinstance(provider, OAuth2Provider):
        raise Http404
    return gateway, provider


class ProtectedResourceMetadataView(View):
    """OAuth 2.0 Protected Resource Metadata (RFC 9728), which MCP clients use to discover
    the authorization server of the gateway"""

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        gateway, provider = gateway_provider(application_slug)
        return JsonResponse(
            {
                "resource": request.build_absolute_uri(
                    reverse(
                        "authentik_providers_mcp:gateway",
                        kwargs={"application_slug": application_slug},
                    )
                ),
                "authorization_servers": [provider.get_issuer(request)],
                "bearer_methods_supported": ["header"],
                "resource_name": gateway.backchannel_application.name,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class GatewayView(View):
    """MCP Streamable HTTP endpoint, serving both protocol eras.

    Requests carrying `_meta` with a protocol version are served statelessly per the
    2026-07-28 revision. `initialize` starts a legacy session, whose ID carries the
    backends' sessions (see `sessions`), so the gateway itself stores nothing."""

    http_method_names = ["post", "delete"]

    gateway: MCPGatewayProvider
    token: AccessToken
    modern: bool
    backend_sessions: dict[str, BackendSession]

    def authenticate(self, request: HttpRequest, application_slug: str) -> HttpResponse | None:
        """Authenticate the request, or return the RFC 9728 §5.1 challenge pointing the
        client at the resource metadata"""
        self.gateway, provider = gateway_provider(application_slug)
        raw_token = validate_auth(request.headers.get("Authorization", "").encode())
        token = (
            AccessToken.filter_not_expired(token=raw_token, provider=provider, revoked=False)
            .select_related("user")
            .first()
            if raw_token
            else None
        )
        if token:
            self.token = token
            return None
        metadata = request.build_absolute_uri(
            reverse(
                "authentik_providers_mcp:protected-resource-metadata",
                kwargs={"application_slug": application_slug},
            )
        )
        response = HttpResponse(status=401)
        response["WWW-Authenticate"] = (
            f'Bearer error="invalid_token", resource_metadata="{metadata}"'
        )
        return response

    def delete(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Terminate a legacy session, and with it the backends' sessions"""
        if response := self.authenticate(request, application_slug):
            return response
        sessions = decode_session(
            request.headers.get(HEADER_SESSION_ID, ""), self.token.user.pk, self.gateway.pk
        )
        if sessions is None:
            return HttpResponse(status=404)
        for backend in self.gateway.backends.filter(pk__in=sessions.keys()):
            client = MCPClient(backend.url, self.backend_token(backend), sessions[str(backend.pk)])
            client.terminate()
            client.http.close()
        return HttpResponse(status=204)

    def post(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        if response := self.authenticate(request, application_slug):
            return response

        try:
            message = jsonrpc_message_adapter.validate_json(request.body)
        except ValidationError:
            return self.reply(
                JSONRPCError(
                    jsonrpc=JSONRPC_VERSION,
                    id=None,
                    error=ErrorData(code=INVALID_REQUEST, message="Invalid JSON-RPC message"),
                ),
                status=400,
            )
        # Notifications and responses don't get a reply
        if not isinstance(message, JSONRPCRequest):
            return HttpResponse(status=202)

        params = message.params or {}
        self.modern = PROTOCOL_VERSION_META_KEY in (params.get("_meta") or {})
        self.backend_sessions = {}
        if not self.modern and message.method != "initialize":
            if session_id := request.headers.get(HEADER_SESSION_ID):
                sessions = decode_session(session_id, self.token.user.pk, self.gateway.pk)
                # Unknown sessions get a 404, upon which clients start a new one
                if sessions is None:
                    return HttpResponse(status=404)
                self.backend_sessions = sessions

        handler = {
            "initialize": self.initialize,
            "server/discover": self.discover,
            "ping": self.ping,
            "tools/list": self.list_tools,
            "tools/call": self.call_tool,
        }.get(message.method)
        try:
            if self.modern:
                self.validate_modern(message)
            if not handler:
                # Modern servers distinguish unknown methods from legacy HTTP+SSE servers
                raise RPCError(
                    METHOD_NOT_FOUND,
                    "Method not found",
                    HTTPStatus.NOT_FOUND if self.modern else HTTPStatus.OK,
                )
            result = handler(params)
        except RPCError as exc:
            return self.reply(
                JSONRPCError(jsonrpc=JSONRPC_VERSION, id=message.id, error=exc.error),
                status=exc.status,
            )
        response = self.reply(
            JSONRPCResponse(jsonrpc=JSONRPC_VERSION, id=message.id, result=result)
        )
        if message.method == "initialize":
            response[HEADER_SESSION_ID] = encode_session(
                self.token.user.pk, self.gateway.pk, self.backend_sessions
            )
        return response

    def reply(self, message: JSONRPCResponse | JSONRPCError, status: int = 200) -> JsonResponse:
        # `exclude_unset` instead of `exclude_none`, as JSON-RPC requires `"id": null`
        return JsonResponse(message.model_dump(mode="json", exclude_unset=True), status=status)

    def validate_modern(self, message: JSONRPCRequest):
        """Validate the headers a 2026-07-28 request mirrors from its body, and its version"""
        params = message.params or {}
        version = params["_meta"][PROTOCOL_VERSION_META_KEY]
        headers = self.request.headers
        mismatched = None
        if headers.get(HEADER_PROTOCOL_VERSION) != version:
            mismatched = HEADER_PROTOCOL_VERSION
        elif headers.get(HEADER_METHOD) != message.method:
            mismatched = HEADER_METHOD
        elif field := NAMED_METHODS.get(message.method):
            try:
                name = decode_header_value(headers.get(HEADER_NAME, ""))
            except ValueError:
                name = None
            if name != params.get(field):
                mismatched = HEADER_NAME
        if mismatched:
            raise RPCError(
                HEADER_MISMATCH, f"Header mismatch: {mismatched} doesn't match body", status=400
            )
        if version not in MODERN_PROTOCOL_VERSIONS:
            raise RPCError(
                UNSUPPORTED_PROTOCOL_VERSION,
                "Unsupported protocol version",
                status=400,
                data={"supported": SUPPORTED_VERSIONS, "requested": version},
            )

    def server_info(self) -> Implementation:
        return Implementation(
            name=self.gateway.backchannel_application.name, version=authentik_version()
        )

    def initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Legacy handshake, which also opens a session with every backend"""
        version = params.get("protocolVersion")
        for backend in self.accessible_backends():
            client = MCPClient(backend.url, self.backend_token(backend))
            try:
                self.backend_sessions[str(backend.pk)] = client.open()
            except MCPClientError as exc:
                LOGGER.warning("Failed to open MCP backend session", backend=backend.slug, exc=exc)
            finally:
                client.http.close()
        return dump(
            InitializeResult(
                protocol_version=(
                    version if version in HANDSHAKE_PROTOCOL_VERSIONS else LATEST_HANDSHAKE_VERSION
                ),
                capabilities=ServerCapabilities(tools=ToolsCapability()),
                server_info=self.server_info(),
            )
        )

    def discover(self, params: dict[str, Any]) -> dict[str, Any]:
        return dump(
            DiscoverResult(
                supported_versions=SUPPORTED_VERSIONS,
                capabilities=ServerCapabilities(tools=ToolsCapability()),
                meta={SERVER_INFO_META_KEY: dump(self.server_info())},
            )
        )

    def ping(self, params: dict[str, Any]) -> dict[str, Any]:
        # Legacy SDKs validate empty results strictly
        return {"resultType": "complete"} if self.modern else {}

    def has_access(self, backend: MCPBackend, tool: str, arguments: dict | None = None) -> bool:
        """Check the backend's policies for a single tool, and that the user can access
        the application the backend issues tokens for"""
        if backend.token_application and not self.has_app_access(backend.token_application):
            return False
        engine = PolicyEngine(backend, self.token.user, self.request)
        # Results depend on the tool and its arguments, which the cache key doesn't include
        engine.use_cache = False
        engine.request.context["mcp"] = {
            "backend": backend.slug,
            "tool": tool,
            "arguments": arguments,
        }
        engine.build()
        return engine.result.passing

    def has_app_access(self, application: Application) -> bool:
        engine = PolicyEngine(application, self.token.user, self.request)
        engine.empty_result = AppAccessWithoutBindings.get()
        engine.build()
        return engine.result.passing

    def accessible_backends(self) -> list[MCPBackend]:
        return [
            backend
            for backend in self.gateway.backends.select_related("token_application")
            if not backend.token_application or self.has_app_access(backend.token_application)
        ]

    def backend_token(self, backend: MCPBackend) -> str | None:
        """Issue a short-lived access token for the user from the backend's linked
        application, carrying over the delegation (`act`) of the gateway token"""
        if not backend.token_application:
            return None
        provider = backend.token_application.get_provider()
        if not isinstance(provider, OAuth2Provider):
            raise MCPClientError("Linked application does not use an OAuth2 provider")
        # ponytail: a new token per backend request, cache unexpired ones if this
        # becomes a hot path
        token = AccessToken(
            provider=provider,
            user=self.token.user,
            actor=self.token.actor,
            expires=now() + timedelta_from_string(backend.token_validity),
            scope=self.token.scope,
            auth_time=self.token.auth_time,
        )
        id_token = IDToken.new(provider, token, self.request, act=self.token.id_token.act)
        # TEMP: akbench (in Docker) only knows authentik as host.docker.internal, revert
        id_token.iss = id_token.iss.replace("//localhost:", "//host.docker.internal:")
        token.id_token = id_token
        token.save()
        return token.token

    def connect(self, backend: MCPBackend) -> MCPClient:
        """Client for a backend, resuming its session if the gateway session has one"""
        return MCPClient(
            backend.url, self.backend_token(backend), self.backend_sessions.get(str(backend.pk))
        )

    def list_tools(self, params: dict[str, Any]) -> dict[str, Any]:
        tools = []
        # ponytail: backends are queried sequentially on every list, parallelize or cache
        # tool lists if gateways with many backends get slow
        for backend in self.accessible_backends():
            try:
                with self.connect(backend) as client:
                    backend_tools = client.list_tools()
            except MCPClientError as exc:
                LOGGER.warning("Failed to list MCP backend tools", backend=backend.slug, exc=exc)
                continue
            for tool in backend_tools:
                if not self.has_access(backend, tool["name"]):
                    continue
                tools.append(
                    {
                        **tool,
                        "name": f"{backend.slug}{TOOL_SEPARATOR}{tool['name']}",
                        # The client sends mirrored parameter headers to the gateway, which
                        # would have to validate them. The backend client adds them instead.
                        "inputSchema": strip_param_headers(tool.get("inputSchema", {})),
                    }
                )
        result: dict[str, Any] = {"tools": tools}
        if self.modern:
            result.update({"resultType": "complete", "ttlMs": 0, "cacheScope": "private"})
        return result

    def call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            call = CallToolRequestParams.model_validate(params)
        except ValidationError as exc:
            raise RPCError(INVALID_PARAMS, "Invalid tool call") from exc
        slug, _, tool = call.name.partition(TOOL_SEPARATOR)
        backend = (
            self.gateway.backends.filter(slug=slug).select_related("token_application").first()
        )
        if not backend or not tool:
            raise RPCError(INVALID_PARAMS, f"Unknown tool: {call.name}")
        arguments = call.arguments or {}

        passing = self.has_access(backend, tool, arguments)
        event = Event.new(
            EventAction.MCP_TOOL_CALL,
            gateway=self.gateway,
            backend=backend,
            tool=tool,
            arguments=arguments,
            passing=passing,
        ).from_http(self.request, user=self.token.user)
        if not passing:
            event.save()
            return tool_error("Access to this tool was denied by policy.")
        # Forward everything but the client's protocol metadata, e.g. `inputResponses`
        # when retrying a call that required input
        forwarded = {key: value for key, value in params.items() if key != "_meta"}
        try:
            with self.connect(backend) as client:
                result = client.call_tool({**forwarded, "name": tool})
        except MCPClientError as exc:
            LOGGER.warning("MCP backend tool call failed", backend=backend.slug, exc=exc)
            event.with_exception(exc).save()
            return tool_error("The tool's server returned an error.")
        event.save()
        return result


def tool_error(text: str) -> dict[str, Any]:
    """Tool execution error, reported in the result so the model can see it"""
    return dump(CallToolResult(content=[TextContent(text=text)], is_error=True))
