"""Client identifier URLs, metadata documents and redirect URIs of public CIMD clients.

Implements draft-ietf-oauth-client-id-metadata-document-03 sections 3-5 for
the public profile: `none` authentication and the authorization code grant.
Parsing is crypto-free: key material is only checked for being public."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from authentik.enterprise.providers.oauth2_cimd.client import CIMDClient
from authentik.enterprise.providers.oauth2_cimd.constants import (
    AUTH_METHOD_NONE,
    DEFAULT_GRANT_TYPES,
    DEFAULT_RESPONSE_TYPES,
    GRANT_AUTHORIZATION_CODE,
    LOOPBACK_REDIRECT_HOSTS,
    MAX_CLIENT_NAME_LENGTH,
    MAX_GRANT_TYPES,
    MAX_JWKS_KEYS,
    MAX_REDIRECT_URIS,
    MAX_RESPONSE_TYPES,
    MAX_SCOPE_TOKENS,
    MAX_SHORT_STRING_LENGTH,
    MAX_URI_LENGTH,
    PUBLIC_GRANT_TYPES,
    PUBLIC_RESPONSE_TYPES,
    RESPONSE_TYPE_CODE,
    SHARED_SECRET_AUTH_METHODS,
)
from authentik.enterprise.providers.oauth2_cimd.errors import (
    InvalidClientID,
    InvalidClientMetadata,
    UnsupportedClient,
)
from authentik.lib.utils.untrusted_fetch import InvalidURL, parse_untrusted_url

# Fields that would carry a shared secret (draft -03 section 4.1)
SECRET_FIELDS = frozenset(("client_secret", "client_secret_expires_at"))
# Fields through which a dynamically registered client manages its own local
# registration. A metadata document can never hold local authority, so they are rejected.
LOCAL_AUTHORITY_FIELDS = frozenset(("registration_access_token", "registration_client_uri"))
# Prefix reserved for local configuration; a document can't set authentik-specific values
LOCAL_FIELD_PREFIXES = ("authentik", "goauthentik")
# Private key members (RFC 7518 section 6) and the symmetric key value
PRIVATE_KEY_MEMBERS = frozenset(("d", "p", "q", "dp", "dq", "qi", "oth", "k"))

# RFC 6749 section 3.3 scope-token
_SCOPE_TOKEN_RE = re.compile(r"^[\x21\x23-\x5b\x5d-\x7e]+$")
_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*$")
_BLOCKED_REDIRECT_SCHEMES = frozenset(("javascript", "data", "vbscript", "file", "blob", "about"))
# Percent-encoded ".", "/" and "\": they hide dot segments and separators from
# path normalization in servers and proxies
_UNSAFE_PATH_ESCAPE_RE = re.compile(r"%(2e|2f|5c)", re.IGNORECASE)
_PORT_RE = re.compile(r"^[0-9]{1,5}$")


@dataclass(frozen=True, slots=True)
class ClientIdentifier:
    """A client identifier URL that passed `parse_client_id()`"""

    url: str
    # The lowercase hostname (IPv6 literals without brackets), for display and admission
    host: str


def parse_client_id(client_id: Any) -> ClientIdentifier:
    """Check that `client_id` is an acceptable client identifier URL (draft -03 section 3).

    Draft rules: https, no userinfo, a path other than `/`, no `.` or `..`
    path segments, no fragment. Local restrictions: no query (the draft says
    SHOULD NOT), no percent-encoded `.`, `/` or `\\` in the path, and the host
    in canonical form (lowercase, no trailing dot, no explicit default port),
    so that one client can't appear under several spellings. Raises InvalidClientID."""
    if not isinstance(client_id, str):
        raise InvalidClientID("invalid_client_id", "Client ID must be a string")
    try:
        parsed = parse_untrusted_url(client_id, MAX_URI_LENGTH)
    except InvalidURL as exc:
        raise InvalidClientID("invalid_client_id", "Client ID is not a valid URL") from exc
    if "?" in client_id:
        raise InvalidClientID("query", "Client ID must not have a query")
    if parsed.path == "/":
        raise InvalidClientID("path_required", "Client ID must have a path")
    if any(segment in (".", "..") for segment in parsed.path.split("/")):
        raise InvalidClientID("dot_segment", "Client ID must not have dot segments")
    if _UNSAFE_PATH_ESCAPE_RE.search(parsed.path):
        raise InvalidClientID("unsafe_escape", "Client ID path has unsafe escapes")
    if urlsplit(client_id).netloc != parsed.host_header:
        raise InvalidClientID("non_canonical_host", "Client ID host is not in canonical form")
    return ClientIdentifier(url=client_id, host=parsed.hostname)


@dataclass(frozen=True, slots=True)
class _RedirectParts:
    scheme: str
    host: str
    path: str
    query: str


def _split_redirect_uri(uri: str) -> _RedirectParts | None:
    """Split a hierarchical redirect URI, keeping the host exactly as written.
    None if it has userinfo, a fragment or an invalid port."""
    try:
        parts = urlsplit(uri)
    except ValueError:
        return None
    if "#" in uri or parts.username is not None or "@" in parts.netloc:
        return None
    netloc = parts.netloc
    if netloc.startswith("["):
        end = netloc.find("]")
        if end == -1:
            return None
        host, rest = netloc[: end + 1], netloc[end + 1 :]
        if rest and not rest.startswith(":"):
            return None
        port = rest[1:] if rest else None
    else:
        host, sep, port_value = netloc.partition(":")
        port = port_value if sep else None
    if port is not None and not (_PORT_RE.match(port) and 0 < int(port) <= 65535):  # noqa: PLR2004
        return None
    # `urlsplit` lowercases the scheme; take it as written
    return _RedirectParts(
        scheme=uri.split(":", 1)[0], host=host, path=parts.path, query=parts.query
    )


def redirect_uri_allowed(registered: Iterable[str], presented: str) -> bool:
    """True if `presented` matches one of the `registered` redirect URIs.

    Matching is exact string comparison, except for plain-HTTP loopback
    redirect URIs (`localhost`, `127.0.0.1`, `[::1]`): those match a
    registered URI with the same scheme, host, path and query on any port
    (RFC 8252 section 7.3, draft -03 section 4.2, decision O1). The host is
    compared as written, so `localhost` doesn't match `127.0.0.1`."""
    registered = tuple(registered)
    if presented in registered:
        return True
    target = _split_redirect_uri(presented)
    if target is None or target.scheme != "http" or target.host not in LOOPBACK_REDIRECT_HOSTS:
        return False
    for uri in registered:
        candidate = _split_redirect_uri(uri)
        if candidate is not None and (
            candidate.scheme,
            candidate.host,
            candidate.path,
            candidate.query,
        ) == (target.scheme, target.host, target.path, target.query):
            return True
    return False


def _str(doc: dict[str, Any], name: str, max_length: int = MAX_SHORT_STRING_LENGTH) -> str | None:
    value = doc.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidClientMetadata("invalid_type", f"{name} must be a string")
    if not value or len(value) > max_length:
        raise InvalidClientMetadata("invalid_value", f"{name} has an invalid length")
    if not value.isprintable():
        raise InvalidClientMetadata("invalid_value", f"{name} contains control characters")
    return value


def _str_list(
    doc: dict[str, Any], name: str, max_items: int, max_length: int = MAX_SHORT_STRING_LENGTH
) -> tuple[str, ...] | None:
    value = doc.get(name)
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise InvalidClientMetadata("invalid_type", f"{name} must be an array of strings")
    if len(value) > max_items:
        raise InvalidClientMetadata("invalid_value", f"{name} has too many entries")
    if any(not item or len(item) > max_length or not item.isprintable() for item in value):
        raise InvalidClientMetadata("invalid_value", f"{name} contains an invalid entry")
    # Keep order, drop duplicates
    return tuple(dict.fromkeys(value))


def _validate_redirect_uri(uri: str) -> None:
    if not uri.isascii() or any(c <= " " or c == "\x7f" for c in uri):
        raise InvalidClientMetadata(
            "invalid_redirect_uri", "Redirect URI contains invalid characters"
        )
    parts = _split_redirect_uri(uri)
    if parts is None:
        raise InvalidClientMetadata("invalid_redirect_uri", "Redirect URI is malformed")
    if not _SCHEME_RE.match(parts.scheme) or parts.scheme in _BLOCKED_REDIRECT_SCHEMES:
        raise InvalidClientMetadata("invalid_redirect_uri", "Redirect URI scheme is not allowed")
    if parts.scheme in ("http", "https"):
        if not parts.host or not uri.startswith(f"{parts.scheme}://"):
            raise InvalidClientMetadata(
                "invalid_redirect_uri", "Redirect URI has an invalid authority"
            )
        # Plain HTTP only on the loopback interface (RFC 8252 section 7.3, RFC 9700)
        if parts.scheme == "http" and parts.host not in LOOPBACK_REDIRECT_HOSTS:
            raise InvalidClientMetadata(
                "invalid_redirect_uri", "HTTP redirect URIs are only allowed for loopback"
            )


def _informative_uri(doc: dict[str, Any], name: str) -> str | None:
    """Display-only URIs: wrong types are rejected, values that aren't HTTPS URLs dropped"""
    value = _str(doc, name, MAX_URI_LENGTH)
    if value is None:
        return None
    try:
        parts = urlsplit(value)
    except ValueError:
        return None
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        return None
    return value


def _check_auth_method(doc: dict[str, Any]) -> None:
    # Draft -03 section 5: the default is `none`, never RFC 7591's `client_secret_basic`
    method = _str(doc, "token_endpoint_auth_method") or AUTH_METHOD_NONE
    if method in SHARED_SECRET_AUTH_METHODS:
        raise InvalidClientMetadata("shared_secret", "Shared-secret authentication is not allowed")
    if method != AUTH_METHOD_NONE:
        # A client that authenticates is never resolved as a public client
        raise UnsupportedClient(
            "auth_method_unsupported", "Only public clients (auth method none) are supported"
        )


def _check_keys(doc: dict[str, Any]) -> None:
    """Keys are unused by public clients. Only check they're public and unambiguous"""
    jwks = doc.get("jwks")
    jwks_uri = doc.get("jwks_uri")
    if jwks is not None and jwks_uri is not None:
        raise InvalidClientMetadata("jwks_conflict", "jwks and jwks_uri are mutually exclusive")
    if jwks_uri is not None:
        _str(doc, "jwks_uri", MAX_URI_LENGTH)
        return
    if jwks is None:
        return
    keys = jwks.get("keys") if isinstance(jwks, dict) else None
    if not isinstance(keys, list) or not all(isinstance(key, dict) for key in keys):
        raise InvalidClientMetadata("malformed_jwks", "jwks must contain a keys array of objects")
    if len(keys) > MAX_JWKS_KEYS:
        raise InvalidClientMetadata("malformed_jwks", "jwks contains too many keys")
    for key in keys:
        if PRIVATE_KEY_MEMBERS & key.keys():
            raise InvalidClientMetadata("private_key", "jwks contains private key material")
        if key.get("kty") == "oct":
            raise InvalidClientMetadata("symmetric_key", "jwks contains a symmetric key")


def _scopes(doc: dict[str, Any]) -> tuple[str, ...] | None:
    scope = _str(doc, "scope", MAX_URI_LENGTH)
    if scope is None:
        return None
    tokens = scope.split(" ")
    if len(tokens) > MAX_SCOPE_TOKENS or not all(_SCOPE_TOKEN_RE.match(t) for t in tokens):
        raise InvalidClientMetadata("invalid_value", "scope is malformed")
    return tuple(dict.fromkeys(tokens))


def _check_prohibited(doc: dict[str, Any]) -> None:
    if SECRET_FIELDS & doc.keys():
        raise InvalidClientMetadata("shared_secret", "Document contains a client secret")
    if LOCAL_AUTHORITY_FIELDS & doc.keys() or any(
        name.lower().startswith(LOCAL_FIELD_PREFIXES) for name in doc
    ):
        raise InvalidClientMetadata("local_authority", "Document claims local configuration")


@dataclass(frozen=True, slots=True)
class ClientMetadata:
    """A validated public client metadata document.

    Holds only the fields authentik uses. Unknown fields (and `logo_uri`,
    which isn't shown until authentik serves it itself) are never exposed."""

    client_id: str
    client_name: str
    client_name_declared: bool
    client_uri: str | None
    policy_uri: str | None
    tos_uri: str | None
    redirect_uris: tuple[str, ...]
    grant_types: tuple[str, ...]
    scopes: tuple[str, ...] | None

    def to_client(self, *, expires_at: float, stale: bool) -> CIMDClient:
        """The picklable client record"""
        return CIMDClient(
            client_id=self.client_id,
            client_name=self.client_name,
            client_name_declared=self.client_name_declared,
            client_uri=self.client_uri,
            policy_uri=self.policy_uri,
            tos_uri=self.tos_uri,
            redirect_uris=self.redirect_uris,
            grant_types=self.grant_types,
            token_endpoint_auth_method=AUTH_METHOD_NONE,
            scopes=self.scopes,
            expires_at=expires_at,
            stale=stale,
        )


def validate_metadata(document: dict[str, Any], client_id: str) -> ClientMetadata:
    """Validate a parsed metadata document fetched from `client_id` as a public client.

    Declared grant and response types outside the public profile are dropped
    (VS Code declares `device_code`); authorization code must remain. Raises
    InvalidClientMetadata for malformed or prohibited documents, and
    UnsupportedClient for valid documents that don't describe a public client."""
    identifier = parse_client_id(client_id)
    if document.get("client_id") != client_id:
        # Simple string comparison, no normalization (draft -03 section 3)
        raise InvalidClientMetadata("client_id_mismatch", "client_id does not match the URL")
    _check_prohibited(document)
    _check_auth_method(document)
    _check_keys(document)
    redirect_uris = _str_list(document, "redirect_uris", MAX_REDIRECT_URIS, MAX_URI_LENGTH) or ()
    for uri in redirect_uris:
        _validate_redirect_uri(uri)
    declared_grants = _str_list(document, "grant_types", MAX_GRANT_TYPES)
    declared_responses = _str_list(document, "response_types", MAX_RESPONSE_TYPES)
    grant_types = tuple(
        grant
        for grant in (DEFAULT_GRANT_TYPES if declared_grants is None else declared_grants)
        if grant in PUBLIC_GRANT_TYPES
    )
    response_types = {
        response
        for response in (
            DEFAULT_RESPONSE_TYPES if declared_responses is None else declared_responses
        )
        if response in PUBLIC_RESPONSE_TYPES
    }
    if GRANT_AUTHORIZATION_CODE not in grant_types or RESPONSE_TYPE_CODE not in response_types:
        raise UnsupportedClient(
            "authorization_code_required", "Client doesn't declare the authorization code grant"
        )
    if not redirect_uris:
        raise UnsupportedClient(
            "redirect_uris_required", "Authorization code requires redirect URIs"
        )
    client_name = _str(document, "client_name", MAX_CLIENT_NAME_LENGTH)
    return ClientMetadata(
        client_id=client_id,
        client_name=client_name or identifier.host,
        client_name_declared=client_name is not None,
        client_uri=_informative_uri(document, "client_uri"),
        policy_uri=_informative_uri(document, "policy_uri"),
        tos_uri=_informative_uri(document, "tos_uri"),
        redirect_uris=redirect_uris,
        grant_types=grant_types,
        scopes=_scopes(document),
    )
