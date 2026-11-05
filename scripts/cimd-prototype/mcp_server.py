# /// script
# requires-python = ">=3.14"
# dependencies = ["mcp==2.3.0", "pyjwt[crypto]>=2.10", "uvicorn>=0.35"]
# ///
"""PROTOTYPE (01b), never merge: a protected MCP server for CIMD interoperability tests.

Points clients at an authentik provider via RFC 9728 protected resource metadata, verifies
authentik-issued JWT access tokens, and logs every request to a JSONL file.

    uv run scripts/cimd-prototype/mcp_server.py \
        --issuer http://localhost:9000/application/o/mcp-proto/ --audience <provider client_id>
"""

import argparse
import json
import os
import socket
import time
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jwt
import uvicorn
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from pydantic import AnyHttpUrl
from starlette.types import ASGIApp, Message, Receive, Scope, Send

LOG = Path(os.environ.get("CIMD_PROTOTYPE_STATE", "/tmp/cimd-prototype")) / "mcp.jsonl"  # nosec


def record(kind: str, **data: Any) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(UTC).isoformat(), "kind": kind, **data}
    with LOG.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, default=str) + "\n")


class JWTVerifier:
    def __init__(self, issuer: str, audience: str, resource: str):
        self.issuer = issuer
        self.audience = audience
        self.resource = resource
        self.jwks = jwt.PyJWKClient(f"{issuer}jwks/")

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256", "ES256", "ES384", "ES512"],
                issuer=self.issuer,
                options={"verify_aud": False},
            )
        except jwt.PyJWTError as exc:
            record("token_rejected", error=str(exc))
            return None
        aud = claims.get("aud")
        audiences = aud if isinstance(aud, list) else [aud]
        if self.audience not in audiences and self.resource not in audiences:
            record("token_rejected", error="invalid_audience", aud=aud)
            return None
        access_token = AccessToken(
            token=token,
            client_id=claims.get("azp") or str(aud),
            scopes=str(claims.get("scope", "")).split(),
            expires_at=claims.get("exp"),
            subject=claims.get("sub"),
            claims=claims,
        )
        record(
            "token_accepted",
            sub=claims.get("sub"),
            azp=claims.get("azp"),
            aud=aud,
            scope=claims.get("scope"),
            exp_in=claims.get("exp", 0) - int(time.time()),
            aud_is_provider=self.audience in audiences,
            aud_is_resource=self.resource in audiences,
        )
        # Prototype: tokens are not resource-bound yet (step 09), so accept the provider
        # audience and record whether the resource was in it.
        return access_token


class RecordRequests:
    """Log each HTTP request's method, path, selected headers and response status"""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        status: dict[str, Any] = {}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
                for key, value in message.get("headers", []):
                    if key.decode().lower() == "www-authenticate":
                        status["www_authenticate"] = value.decode()
            await send(message)

        await self.app(scope, receive, send_wrapper)
        record(
            "http",
            method=scope["method"],
            path=scope["path"],
            query=scope.get("query_string", b"").decode(),
            user_agent=headers.get("user-agent"),
            mcp_protocol_version=headers.get("mcp-protocol-version"),
            mcp_session=bool(headers.get("mcp-session-id")),
            authorization=headers.get("authorization", "").split(" ", 1)[0] or None,
            dpop=bool(headers.get("dpop")),
            **status,
        )


def serve(app: ASGIApp, port: int) -> None:
    """Serve both localhost address families without wildcard listeners."""
    with ExitStack() as stack:
        sockets = []
        for family, address in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
            listener = stack.enter_context(socket.socket(family, socket.SOCK_STREAM))
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if family == socket.AF_INET6:
                listener.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            listener.bind((address, port))
            sockets.append(listener)
        uvicorn.Server(uvicorn.Config(app, log_level="info")).run(sockets=sockets)


def create_app(issuer: str, audience: str, port: int = 8765) -> RecordRequests:
    """Build the probe application without starting its listeners."""
    resource = f"http://localhost:{port}/mcp"

    server: MCPServer[None] = MCPServer(
        name="authentik CIMD prototype",
        token_verifier=JWTVerifier(issuer, audience, resource),
        # Tokens are not resource-bound until step 09; the verifier records the audience
        auth=AuthSettings(
            issuer_url=AnyHttpUrl(issuer),
            resource_server_url=AnyHttpUrl(resource),
            validate_token_resource=False,
        ),
    )

    @server.tool()
    def whoami() -> dict[str, Any]:
        """Return the authenticated subject and token details"""
        token = get_access_token()
        claims = (token.claims or {}) if token else {}
        return {
            "sub": claims.get("sub"),
            "preferred_username": claims.get("preferred_username"),
            "email": claims.get("email"),
            "client": token.client_id if token else None,
            "scopes": token.scopes if token else [],
        }

    @server.tool()
    def echo(text: str) -> str:
        """Echo text back"""
        return text

    app = server.streamable_http_app(host="localhost")
    return RecordRequests(app)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--audience", required=True, help="authentik provider client_id")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve(create_app(args.issuer, args.audience, args.port), args.port)


if __name__ == "__main__":
    main()
