from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

import dns.resolver
from dns.exception import DNSException

from authentik.lib.utils.http import get_http_session

# NOTE: no host/IP validation is performed on these, making them SSRF-susceptible


def _resolve_handle_dns(handle: str) -> str | None:
    try:
        answers = dns.resolver.resolve(f"_atproto.{handle}", "TXT")
    except DNSException:
        return None

    for rdata in answers:
        txt = b"".join(rdata.strings).decode()
        if txt.startswith("did="):
            return txt.removeprefix("did=")
    return None


def _resolve_handle_http(handle: str) -> str | None:
    resp = get_http_session().get(f"https://{handle}/.well-known/atproto-did")
    if not resp.ok:
        return None
    did = resp.text.strip()
    if did.startswith("did:"):
        return did
    return None


def resolve_handle(handle: str) -> str:
    did = _resolve_handle_dns(handle) or _resolve_handle_http(handle)
    if did is None:
        raise ResolutionError(f"Could not resolve handle '{handle}' to a DID.")
    return did


def resolve_did(did: str) -> dict[str, Any]:
    if did.startswith("did:plc:"):
        resp = get_http_session().get(f"https://plc.directory/{did}")
    elif did.startswith("did:web:"):
        domain = did.removeprefix("did:web:").replace(":", "/")
        resp = get_http_session().get(f"https://{unquote(domain)}/.well-known/did.json")
    else:
        raise ResolutionError(f"Unsupported DID method: {did}")
    resp.raise_for_status()
    doc: dict[str, Any] = resp.json()
    return doc


def get_pds_endpoint(diddoc: dict[str, Any]) -> str:
    pds_service = next((s for s in diddoc["service"] if s["id"] == "#atproto_pds"), None)
    if not pds_service:
        raise ResolutionError("Unable to resolve PDS")

    endpoint: str = pds_service["serviceEndpoint"]
    return endpoint


def get_authserver_url(pds_url: str) -> str:
    resp = get_http_session().get(f"{pds_url}/.well-known/oauth-protected-resource")
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()

    url: str = data["authorization_servers"][0]
    return url


def get_authserver_metadata(authserver_url: str) -> dict[str, Any]:
    resp = get_http_session().get(f"{authserver_url}/.well-known/oauth-authorization-server")
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()

    if (
        not data["require_pushed_authorization_requests"]
        or "private_key_jwt" not in data["token_endpoint_auth_methods_supported"]
    ):
        raise ResolutionError(
            f"Authserver {authserver_url} doesn't support the required OAuth flow"
        )

    return data


def resolve_identity(identifier: str) -> ResolvedIdentity:
    is_handle = not identifier.startswith("did:")
    did = resolve_handle(identifier) if is_handle else identifier
    diddoc = resolve_did(did)
    aka = diddoc.get("alsoKnownAs", [])
    if is_handle:
        if f"at://{identifier}" not in aka:
            raise ResolutionError("DID document does not claim this handle.")
        handle = identifier
    else:
        handle = next((h.removeprefix("at://") for h in aka if h.startswith("at://")), did)
    pds_url = get_pds_endpoint(diddoc)
    authserver_url = get_authserver_url(pds_url)
    authserver_metadata = get_authserver_metadata(authserver_url)
    return ResolvedIdentity(did, handle, pds_url, authserver_url, authserver_metadata)


@dataclass
class ResolvedIdentity:
    did: str
    handle: str
    pds_url: str
    authserver_url: str
    authserver_metadata: dict[str, Any]


class ResolutionError(Exception):
    """Error raised when atproto identifier resolution fails"""
