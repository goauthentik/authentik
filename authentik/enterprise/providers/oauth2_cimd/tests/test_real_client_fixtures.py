"""Compatibility with metadata documents captured from real clients.

The documents and response headers under `fixtures/real_clients` were captured
from Claude Code and VS Code (see `manifest.json` for provenance). They are
served from a mock transport; nothing here touches the network.

These tests cover document validation, profile negotiation and cache freshness
only. They make no claim about authorization-time behavior such as redirect URI
matching, scope defaults or refresh token handling."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from django.test import SimpleTestCase

from authentik.enterprise.providers.oauth2_cimd.constants import (
    AUTH_METHOD_NONE,
    GRANT_AUTHORIZATION_CODE,
    GRANT_DEVICE_CODE,
    GRANT_REFRESH_TOKEN,
    RESPONSE_TYPE_CODE,
)
from authentik.enterprise.providers.oauth2_cimd.errors import UnsupportedClient
from authentik.enterprise.providers.oauth2_cimd.metadata import validate_metadata
from authentik.enterprise.providers.oauth2_cimd.negotiation import (
    MANAGED_PROFILE,
    PUBLIC_PROFILE,
    negotiate,
)
from authentik.enterprise.providers.oauth2_cimd.tests.utils import START, make_service
from authentik.lib.utils.untrusted_fetch.testing import MockResponse

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "real_clients"


@dataclass(frozen=True)
class CapturedClient:
    """A captured metadata document and the response headers it was served with"""

    name: str
    client_id: str
    status: int
    headers: dict[str, str]
    body: bytes

    @property
    def document(self) -> dict[str, Any]:
        return json.loads(self.body)

    def response(self) -> MockResponse:
        return MockResponse(status=self.status, headers=dict(self.headers), body=self.body)


def load_clients() -> dict[str, CapturedClient]:
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    return {
        name: CapturedClient(
            name=name,
            client_id=entry["url"],
            status=entry["status"],
            headers=entry["headers"],
            body=(FIXTURES / entry["document"]).read_bytes(),
        )
        for name, entry in manifest["clients"].items()
    }


CLIENTS = load_clients()
CLAUDE_CODE = CLIENTS["claude_code"]
VSCODE = CLIENTS["vscode"]

CLAUDE_CODE_REDIRECT_URIS = ("http://localhost/callback", "http://127.0.0.1/callback")
VSCODE_REDIRECT_URIS = ("http://127.0.0.1:33418/", "https://vscode.dev/redirect")
PUBLIC_GRANTS = frozenset((GRANT_AUTHORIZATION_CODE, GRANT_REFRESH_TOKEN))


def serve(client: CapturedClient):
    """A service that serves only `client`'s captured document"""
    return make_service({client.client_id: client.response()})


def requested(transport) -> list[tuple[str, str]]:
    return [(request.hostname, request.path) for request in transport.requests]


def metadata_request(client: CapturedClient) -> tuple[str, str]:
    parts = urlsplit(client.client_id)
    if parts.hostname is None:
        raise ValueError("Captured client URL must have a hostname")
    return parts.hostname, parts.path


class TestFixtures(SimpleTestCase):
    """The checked-in captures are what the tests below assume"""

    def test_manifest(self):
        self.assertEqual(set(CLIENTS), {"claude_code", "vscode"})
        for client in CLIENTS.values():
            with self.subTest(client=client.name):
                self.assertEqual(client.status, 200)
                self.assertEqual(client.document["client_id"], client.client_id)
                self.assertEqual(set(client.headers), {"Content-Type", "Cache-Control"})

    def test_captured_headers(self):
        self.assertEqual(CLAUDE_CODE.headers["Content-Type"], "application/json")
        self.assertEqual(CLAUDE_CODE.headers["Cache-Control"], "public, max-age=300")
        self.assertEqual(VSCODE.headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(VSCODE.headers["Cache-Control"], "no-store,no-cache,max-age=0")


class TestValidation(SimpleTestCase):
    """The captured documents validate as keyless public clients"""

    def test_claude_code(self):
        metadata = validate_metadata(CLAUDE_CODE.document, CLAUDE_CODE.client_id)
        self.assertEqual(metadata.client_name, "Claude Code")
        self.assertEqual(metadata.redirect_uris, CLAUDE_CODE_REDIRECT_URIS)
        self.assertEqual(metadata.grant_types, (GRANT_AUTHORIZATION_CODE, GRANT_REFRESH_TOKEN))
        self.assertEqual(metadata.response_types, (RESPONSE_TYPE_CODE,))
        self.assertEqual(metadata.token_endpoint_auth_methods, (AUTH_METHOD_NONE,))
        self.assertEqual(metadata.client_uri, "https://claude.ai")
        self.assertIsNone(metadata.logo_uri)
        self.assertFalse(metadata.has_keys)

    def test_vscode(self):
        metadata = validate_metadata(VSCODE.document, VSCODE.client_id)
        self.assertEqual(metadata.client_name, "Visual Studio Code")
        self.assertEqual(metadata.redirect_uris, VSCODE_REDIRECT_URIS)
        self.assertEqual(
            metadata.grant_types,
            (GRANT_AUTHORIZATION_CODE, GRANT_REFRESH_TOKEN, GRANT_DEVICE_CODE),
        )
        self.assertEqual(metadata.response_types, (RESPONSE_TYPE_CODE,))
        self.assertEqual(metadata.token_endpoint_auth_methods, (AUTH_METHOD_NONE,))
        self.assertEqual(metadata.client_uri, "https://vscode.dev/product")
        self.assertEqual(
            metadata.logo_uri, "https://code.visualstudio.com/assets/branding/code-stable.png"
        )
        self.assertFalse(metadata.has_keys)

    def test_public_negotiation(self):
        for client in CLIENTS.values():
            with self.subTest(client=client.name):
                metadata = validate_metadata(client.document, client.client_id)
                capabilities = negotiate(metadata, PUBLIC_PROFILE)
                self.assertEqual(capabilities.token_endpoint_auth_method, AUTH_METHOD_NONE)
                self.assertEqual(capabilities.grant_types, PUBLIC_GRANTS)
                self.assertNotIn(GRANT_DEVICE_CODE, capabilities.grant_types)
                self.assertEqual(capabilities.redirect_uris, metadata.redirect_uris)

    def test_managed_negotiation(self):
        """A keyless public document is never downgraded into the managed profile"""
        for client in CLIENTS.values():
            with self.subTest(client=client.name):
                metadata = validate_metadata(client.document, client.client_id)
                with self.assertRaises(UnsupportedClient) as ctx:
                    negotiate(metadata, MANAGED_PROFILE)
                self.assertEqual(ctx.exception.code, "auth_method_unsupported")


class TestResolution(SimpleTestCase):
    """Resolving the captured documents through the service"""

    def test_resolve_public(self):
        expected_redirects = {
            CLAUDE_CODE.name: CLAUDE_CODE_REDIRECT_URIS,
            VSCODE.name: VSCODE_REDIRECT_URIS,
        }
        for client in CLIENTS.values():
            with self.subTest(client=client.name):
                service, transport, _ = serve(client)
                resolved = service.resolve(client.client_id, PUBLIC_PROFILE)
                self.assertEqual(resolved.metadata.client_id, client.client_id)
                self.assertEqual(resolved.capabilities.token_endpoint_auth_method, "none")
                self.assertFalse(resolved.capabilities.confidential)
                self.assertEqual(resolved.capabilities.grant_types, PUBLIC_GRANTS)
                self.assertEqual(
                    resolved.capabilities.redirect_uris, expected_redirects[client.name]
                )
                self.assertIsNone(resolved.keys)
                self.assertEqual(requested(transport), [metadata_request(client)])

    def test_content_type_charset(self):
        """VS Code serves `application/json; charset=utf-8`"""
        service, _, _ = serve(VSCODE)
        resolved = service.resolve(VSCODE.client_id, PUBLIC_PROFILE)
        self.assertEqual(resolved.metadata.redirect_uris, VSCODE_REDIRECT_URIS)

    def test_resolve_managed(self):
        for client in CLIENTS.values():
            with self.subTest(client=client.name):
                service, transport, _ = serve(client)
                with self.assertRaises(UnsupportedClient) as ctx:
                    service.resolve(client.client_id, MANAGED_PROFILE)
                self.assertEqual(ctx.exception.code, "auth_method_unsupported")
                self.assertEqual(requested(transport), [metadata_request(client)])


class TestCaching(SimpleTestCase):
    """Freshness derived from the captured Cache-Control headers"""

    def assert_cached_for(self, client: CapturedClient, ttl: int):
        service, transport, clock = serve(client)
        resolved = service.resolve(client.client_id, PUBLIC_PROFILE)
        self.assertEqual(resolved.expires_at, START + ttl)
        self.assertEqual(len(transport.requests), 1)
        clock.advance(ttl - 1)
        service.resolve(client.client_id, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 1)
        clock.advance(1)
        refreshed = service.resolve(client.client_id, PUBLIC_PROFILE)
        self.assertEqual(len(transport.requests), 2)
        self.assertEqual(refreshed.expires_at, START + 2 * ttl)

    def test_claude_code_max_age(self):
        """`public, max-age=300` is cached up to the 300-second ceiling"""
        self.assert_cached_for(CLAUDE_CODE, 300)

    def test_vscode_no_store(self):
        """`no-store,no-cache,max-age=0` is still cached for the 60-second minimum"""
        self.assert_cached_for(VSCODE, 60)
