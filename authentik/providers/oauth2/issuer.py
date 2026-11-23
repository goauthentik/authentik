"""Canonical issuer for checks that bind a token to this authorization server.

`OAuth2Provider.get_issuer` builds the issuer from the request's `Host` header, which any
client can set. That is fine for discovery and for tokens authentik issues, but not for
checks that accept a token because its audience names this server (an ID-JAG's `aud`, a
client assertion's `aud`): a token minted for an authorization server at another host,
with the same provider path, would be accepted by sending that host in the `Host` header.

A request host is only trusted as part of the issuer when the administrator has said it
belongs to this instance:
- when `providers.oauth2.trusted_issuer_origins` is set, the request origin (scheme, host
  and port) must be one of the listed origins, and nothing else is trusted;
- otherwise the host must match the domain of a brand (exactly, or as a subdomain, as brands
  match hosts). A host that only reaches the default brand as the fallback for unknown hosts
  is not trusted.
"""

from urllib.parse import urlsplit

from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()

CONFIG_TRUSTED_ISSUER_ORIGINS = "providers.oauth2.trusted_issuer_origins"
DEFAULT_PORTS = {"http": 80, "https": 443}


class UntrustedIssuer(Exception):
    """The request can't be trusted to name this authorization server's issuer"""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def normalize_origin(value: str) -> str | None:
    """`scheme://host[:port]` with the scheme and host lowercased and a default port dropped,
    or None when `value` isn't an http(s) origin. A trailing `/` is allowed; any other path,
    a query, a fragment or userinfo is not."""
    try:
        parts = urlsplit(value.strip())
        port = parts.port
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    host = parts.hostname
    if scheme not in DEFAULT_PORTS or not host:
        return None
    if parts.username is not None or parts.password is not None:
        return None
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        return None
    if ":" in host:
        host = f"[{host}]"
    if port is None or port == DEFAULT_PORTS[scheme]:
        return f"{scheme}://{host}"
    return f"{scheme}://{host}:{port}"


def trusted_issuer_origins() -> frozenset[str]:
    """The configured origins, normalized. Entries that aren't origins are ignored (and
    logged), so they can't widen what is trusted."""
    raw = CONFIG.get(CONFIG_TRUSTED_ISSUER_ORIGINS, [])
    if isinstance(raw, str):
        raw = raw.split(",")
    origins = set()
    for entry in raw or []:
        if not isinstance(entry, str) or not entry.strip():
            continue
        origin = normalize_origin(entry)
        if origin is None:
            LOGGER.warning("Ignoring invalid trusted issuer origin", origin=entry)
            continue
        origins.add(origin)
    return frozenset(origins)


def host_matches_domain(host: str, domain: str) -> bool:
    """Whether a brand with `domain` matches `host`, mirroring `get_brand_for_request`"""
    host = host.lower()
    domain = domain.lower()
    if not domain:
        return False
    return host == domain or host.endswith(f".{domain}")


def check_issuer_host(request: HttpRequest) -> None:
    """Raise `UntrustedIssuer` unless the request's host may be used in the issuer for
    issuer-sensitive checks (see the module docstring)."""
    from authentik.brands.utils import get_brand_for_request

    origins = trusted_issuer_origins()
    if origins:
        if normalize_origin(f"{request.scheme}://{request.get_host()}") not in origins:
            raise UntrustedIssuer("origin_not_trusted")
        return
    brand = get_brand_for_request(request)
    # The unsaved fallback brand stands in when no brand exists at all
    if brand._state.adding or not host_matches_domain(request.get_host(), brand.domain):
        raise UntrustedIssuer("host_not_trusted")
