"""CIMD test fixtures. Nothing here touches the network."""

import json
from functools import cache
from typing import Any

from django.core.cache.backends.locmem import LocMemCache
from jwcrypto.jwk import JWK

from authentik.enterprise.providers.oauth2_cimd.service import ClientMetadataService
from authentik.lib.generators import generate_id
from authentik.lib.utils.untrusted_fetch.testing import FakeClock, MockResponse, mock_fetcher

CLIENT_ID = "https://client.example.com/oauth/client.json"
JWKS_URI = "https://client.example.com/oauth/jwks.json"
REDIRECT_URI = "http://127.0.0.1/callback"
# Wall-clock start for FakeClock, in 2027
START = 1_800_000_000.0


@cache
def _private_key(kind: str, index: int) -> JWK:
    if kind == "RSA":
        return JWK.generate(kty="RSA", size=2048)
    if kind == "EC":
        return JWK.generate(kty="EC", crv="P-256")
    if kind == "OKP":
        return JWK.generate(kty="OKP", crv="Ed25519")
    raise ValueError(kind)


def public_jwk(kind: str = "RSA", index: int = 0, **extra: Any) -> dict[str, Any]:
    """A public JWK; the same (kind, index) always gives the same key"""
    return _private_key(kind, index).export_public(as_dict=True) | extra


def private_jwk(kind: str = "RSA", index: int = 0) -> dict[str, Any]:
    """The private JWK matching `public_jwk(kind, index)`"""
    return _private_key(kind, index).export_private(as_dict=True)


def public_document(**overrides: Any) -> dict[str, Any]:
    """A valid keyless public client document"""
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


def managed_document(**overrides: Any) -> dict[str, Any]:
    """A valid managed client document using jwks_uri"""
    values: dict[str, Any] = {
        "token_endpoint_auth_method": None,
        "token_endpoint_auth_methods_supported": ["private_key_jwt"],
        "grant_types": ["authorization_code", "refresh_token", "client_credentials"],
        "jwks_uri": JWKS_URI,
    }
    return public_document(**(values | overrides))


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


def make_service(responses=None, *, clock: FakeClock | None = None, shared_cache=None, **kwargs):
    """A service with a mock fetcher, its own in-memory cache and a fake clock.

    Pass `shared_cache` to model several workers sharing one cache."""
    clock = clock or FakeClock(START)
    fetcher, transport = mock_fetcher(responses, clock=clock)
    backend = shared_cache if shared_cache is not None else new_cache()
    kwargs.setdefault("local_check", lambda _client_id: True)
    service = ClientMetadataService(
        cache_backend=backend,
        fetcher=fetcher,
        clock=clock,
        sleep_func=clock.advance,
        **kwargs,
    )
    return service, transport, clock


def new_cache() -> LocMemCache:
    """An isolated in-memory cache"""
    return LocMemCache(f"cimd-test-{generate_id()}", {})


def requested_paths(transport) -> list[str]:
    """Paths requested from the mock transport, in order"""
    return [request.path for request in transport.requests]
