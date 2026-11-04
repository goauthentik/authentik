"""PROTOTYPE (01b), never merge: CIMD interoperability probe.

Deliberately minimal and unhardened. It lets real MCP clients use a URL-valued client_id
against one scoped provider and records everything they send, so we can write down what
clients actually do. No admission rules, no SSRF protection, naive caching, no client
binding on grants. See CIMD_DESIGN.md step 01b.

Enabled per application slug:
    AUTHENTIK_CIMD_PROTOTYPE__APPLICATIONS=mcp-proto
    AUTHENTIK_CIMD_PROTOTYPE__LOG=/tmp/cimd-prototype/requests.jsonl
    AUTHENTIK_CIMD_PROTOTYPE__ALLOW_HTTP_LOCALHOST=true   # for local test metadata
"""

from dataclasses import dataclass, field
from hashlib import sha256
from json import JSONDecodeError, dumps, loads
from pathlib import Path
from threading import Lock
from time import time
from typing import Any
from urllib.parse import urlparse

import requests
from django.http import Http404, HttpRequest, HttpResponse
from django.utils.timezone import now
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.lib.config import CONFIG
from authentik.providers.oauth2.client import (
    ClientAdapter,
    LegacyClientAdapter,
    OAuthClientContext,
    OAuthClientResolver,
    ProviderSelector,
)
from authentik.providers.oauth2.models import (
    ClientType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)

LOGGER = get_logger()
# Registration kind of clients identified by a Client ID Metadata Document URL
METADATA_KIND = "metadata"
LOOPBACK_HOSTS = {"127.0.0.1", "[::1]", "::1", "localhost"}
CACHE_SECONDS = 300
_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_log_lock = Lock()

# Request/response fields whose values are secrets: record a short hash instead, so reuse
# (e.g. concurrent refreshes with the same refresh token) is still visible in the log.
SECRET_FIELDS = {
    "code",
    "code_verifier",
    "refresh_token",
    "access_token",
    "id_token",
    "client_secret",
    "client_assertion",
    "assertion",
    "password",
    "token",
}


def enabled_slugs() -> set[str]:
    raw = CONFIG.get("cimd_prototype.applications", "") or ""
    return {slug.strip() for slug in str(raw).split(",") if slug.strip()}


def is_enabled(provider: OAuth2Provider) -> bool:
    try:
        return provider.application.slug in enabled_slugs()
    except Application.DoesNotExist:
        return False


def scoped_provider(application_slug: str) -> OAuth2Provider:
    """Provider for a CIMD-enabled scoped endpoint, else 404"""
    if application_slug not in enabled_slugs():
        raise Http404
    application = Application.objects.filter(slug=application_slug).first()
    if not application:
        raise Http404
    provider = OAuth2Provider.objects.filter(pk=application.provider_id).first()
    if not provider:
        raise Http404
    return provider


def short_hash(value: str) -> str:
    return sha256(value.encode()).hexdigest()[:12]


def record(kind: str, **data: Any) -> None:
    """Append one observation to the prototype log"""
    path = CONFIG.get("cimd_prototype.log", "/tmp/cimd-prototype/requests.jsonl")  # nosec
    entry = {"ts": now().isoformat(), "kind": kind, **data}
    with _log_lock:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as log:
            log.write(dumps(entry, default=str) + "\n")


def redact(values: dict[str, Any]) -> dict[str, Any]:
    redacted = {}
    for key, value in values.items():
        if key in SECRET_FIELDS and isinstance(value, str) and value:
            redacted[key] = {"sha": short_hash(value), "len": len(value)}
        else:
            redacted[key] = value
    return redacted


def is_metadata_url(client_id: str) -> bool:
    parsed = urlparse(client_id)
    if parsed.scheme == "https" and parsed.netloc and parsed.path not in ("", "/"):
        return True
    return (
        bool(CONFIG.get_bool("cimd_prototype.allow_http_localhost", False))
        and parsed.scheme == "http"
        and parsed.hostname in LOOPBACK_HOSTS
    )


def fetch_metadata(client_id: str) -> dict[str, Any] | None:
    """Fetch a client metadata document. Naive: no SSRF checks, fixed-time cache."""
    cached = _cache.get(client_id)
    if cached and cached[0] > time():
        return cached[1]
    try:
        response = requests.get(
            client_id,
            timeout=5,
            allow_redirects=False,
            headers={"Accept": "application/json"},
        )
    except requests.RequestException as exc:
        record("metadata_fetch", client_id=client_id, error=str(exc))
        return None
    try:
        document = response.json()
    except JSONDecodeError, ValueError:
        document = None
    record(
        "metadata_fetch",
        client_id=client_id,
        status=response.status_code,
        headers={
            key: response.headers.get(key)
            for key in ("Content-Type", "Cache-Control", "ETag", "Expires", "Location")
            if response.headers.get(key)
        },
        document=document if document is not None else response.text[:2000],
    )
    if response.status_code != 200 or not isinstance(document, dict):  # noqa: PLR2004
        return None
    if document.get("client_id") != client_id:
        record("metadata_invalid", client_id=client_id, reason="client_id mismatch")
        return None
    _cache[client_id] = (time() + CACHE_SECONDS, document)
    return document


@dataclass(frozen=True, slots=True)
class PrototypeMetadataClientContext(OAuthClientContext):
    """A client described by a fetched metadata document"""

    # Raw redirect URIs from the document, matched by `match_redirect_uri`
    metadata_redirect_uris: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class PrototypeScopedProviderSelector(ProviderSelector):
    """Always select the provider of the scoped endpoint"""

    def __init__(self, provider: OAuth2Provider):
        self.provider = provider

    def select(self, request: HttpRequest | None, client_id: str) -> OAuth2Provider | None:
        return self.provider


class PrototypeMetadataClientAdapter(ClientAdapter):
    """Resolve a CIMD URL within the selected provider"""

    def resolve(
        self, request: HttpRequest | None, provider: OAuth2Provider, client_id: str
    ) -> OAuthClientContext | None:
        if not is_metadata_url(client_id):
            record("client_unresolved", client_id=client_id, reason="not a metadata URL")
            return None
        document = fetch_metadata(client_id)
        if document is None:
            return None
        redirect_uris = tuple(
            uri for uri in (document.get("redirect_uris") or []) if isinstance(uri, str)
        )
        return PrototypeMetadataClientContext(
            provider=provider,
            client_id=client_id,
            registration_kind=METADATA_KIND,
            client_type=ClientType.PUBLIC,
            redirect_uris=tuple(
                RedirectURI(RedirectURIMatchingMode.STRICT, uri) for uri in redirect_uris
            ),
            # Grant types are still governed by the provider in the prototype
            grant_types=frozenset(provider.grant_types),
            metadata_redirect_uris=redirect_uris,
            metadata=document,
        )


def scoped_resolver(provider: OAuth2Provider) -> OAuthClientResolver:
    """Resolve the provider's own client, else a CIMD URL, within one provider"""
    return OAuthClientResolver(
        PrototypeScopedProviderSelector(provider),
        [LegacyClientAdapter(), PrototypeMetadataClientAdapter()],
    )


def is_metadata_client(client: OAuthClientContext | None) -> bool:
    return isinstance(client, PrototypeMetadataClientContext)


def match_redirect_uri(client: OAuthClientContext, redirect_uri: str) -> str | None:
    """Match against the document's redirect URIs. Returns how it matched, or None.

    Exact match, or RFC 8252 section 7.3: loopback redirects may differ only in port."""
    if not isinstance(client, PrototypeMetadataClientContext):
        return None
    if redirect_uri in client.metadata_redirect_uris:
        return "exact"
    requested = urlparse(redirect_uri)
    for allowed_uri in client.metadata_redirect_uris:
        allowed = urlparse(allowed_uri)
        if (
            requested.scheme == allowed.scheme == "http"
            and requested.hostname == allowed.hostname
            and requested.hostname in LOOPBACK_HOSTS
            and requested.path == allowed.path
            and requested.query == allowed.query
        ):
            return "loopback_port_variance"
    return None


def cors_allow_any(request: HttpRequest, response: HttpResponse) -> HttpResponse:
    """Reflect any origin, so browser-based clients can probe discovery and the token
    endpoint. Prototype only."""
    origin = request.META.get("HTTP_ORIGIN")
    if origin:
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Headers"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


RECORDED_HEADERS = (
    "User-Agent",
    "Accept",
    "Origin",
    "Content-Type",
    "MCP-Protocol-Version",
    "DPoP",
)


class PrototypeRecordingMiddleware:
    """Record OAuth discovery and protocol traffic, including 404s from discovery probes"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not (
            request.path.startswith("/.well-known/")
            or (request.path.startswith("/application/o/") and "/api/" not in request.path)
        ):
            return self.get_response(request)
        started = time()
        form = redact(request.POST.dict()) if request.method == "POST" else {}
        response = self.get_response(request)
        headers = {}
        for header in RECORDED_HEADERS:
            value = request.headers.get(header)
            if value:
                headers[header] = "<present>" if header == "DPoP" else value
        authorization = request.headers.get("Authorization", "")
        if authorization:
            headers["Authorization"] = authorization.split(" ", 1)[0] + " <redacted>"
        body = None
        if response.get("Content-Type", "").startswith("application/json"):
            try:
                body = redact(loads(response.content))
            except ValueError, AttributeError:
                body = None
        record(
            "http",
            method=request.method,
            path=request.path,
            query=redact(request.GET.dict()),
            form=form,
            headers=headers,
            status=response.status_code,
            location=response.get("Location"),
            response=body if request.path.endswith("/token/") else None,
            ms=int((time() - started) * 1000),
        )
        return response
