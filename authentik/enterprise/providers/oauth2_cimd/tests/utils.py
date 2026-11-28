"""CIMD test fixtures. Nothing here touches the network."""

import json
from typing import Any

from django.core.cache.backends.locmem import LocMemCache

from authentik.enterprise.providers.oauth2_cimd.resolver import PublicClientResolver
from authentik.lib.generators import generate_id
from authentik.lib.utils.untrusted_fetch.testing import FakeClock, MockResponse, mock_fetcher

CLIENT_ID = "https://client.example.com/oauth/client.json"
REDIRECT_URI = "http://127.0.0.1/callback"
# Wall-clock start for FakeClock, in 2027
START = 1_800_000_000.0


def public_document(**overrides: Any) -> dict[str, Any]:
    """A valid keyless public client document. A None override removes the field"""
    document: dict[str, Any] = {
        "client_id": CLIENT_ID,
        "client_name": "Example MCP client",
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    }
    document.update(overrides)
    return {key: value for key, value in document.items() if value is not None}


def json_response(
    body: dict[str, Any] | bytes,
    *,
    cache_control: str | None = None,
    content_type: str = "application/json",
    headers: dict[str, str] | None = None,
) -> MockResponse:
    """A 200 JSON response"""
    all_headers = {"Content-Type": content_type}
    if cache_control is not None:
        all_headers["Cache-Control"] = cache_control
    all_headers.update(headers or {})
    content = body if isinstance(body, bytes) else json.dumps(body).encode()
    return MockResponse(status=200, headers=all_headers, body=content)


def new_cache() -> LocMemCache:
    """An isolated in-memory cache"""
    return LocMemCache(f"cimd-test-{generate_id()}", {})


def make_resolver(responses=None, *, clock: FakeClock | None = None, shared_cache=None, **kwargs):
    """A resolver with a mock fetcher, its own in-memory cache and a fake clock.

    Pass `shared_cache` to model several workers sharing one cache."""
    clock = clock or FakeClock(START)
    fetcher, transport = mock_fetcher(responses, clock=clock, **kwargs)
    resolver = PublicClientResolver(
        cache_backend=shared_cache if shared_cache is not None else new_cache(),
        fetcher=fetcher,
        clock=clock,
    )
    return resolver, transport, clock


def admit_all(_client_id: str) -> bool:
    """Admission check that admits every client"""
    return True
