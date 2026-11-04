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
import time
from datetime import UTC, datetime
from pathlib import Path

import jwt
import uvicorn
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from starlette.types import ASGIApp, Receive, Scope, Send

LOG = Path("/tmp/cimd-prototype/mcp.jsonl")  # nosec


def record(kind: str, **data):
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
        if self.audience not in audiences and self.resource not in audiences:
            return None
        return AccessToken(
            token=token,
            client_id=claims.get("azp") or str(aud),
            scopes=str(claims.get("scope", "")).split(),
            expires_at=claims.get("exp"),
            subject=claims.get("sub"),
            claims=claims,
        )


class RecordRequests:
    """Log each HTTP request's method, path, selected headers and response status"""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        status = {}

        async def send_wrapper(message):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--audience", required=True, help="authentik provider client_id")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    resource = f"http://localhost:{args.port}/mcp"

    server = MCPServer(
        name="authentik CIMD prototype",
        token_verifier=JWTVerifier(args.issuer, args.audience, resource),
        # Tokens are not resource-bound until step 09; the verifier records the audience
        auth=AuthSettings(
            issuer_url=args.issuer,
            resource_server_url=resource,
            validate_token_resource=False,
        ),
    )

    @server.tool()
    def whoami() -> dict:
        """Return the authenticated subject and token details"""
        token = get_access_token()
        claims = token.claims if token else {}
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
    uvicorn.run(RecordRequests(app), host="::", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
