"""Typed validation of Client ID Metadata Documents (draft -03 sections 3-5)"""

import re
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlsplit

from authentik.enterprise.providers.oauth2_cimd.constants import (
    AUTH_METHOD_NONE,
    DEFAULT_GRANT_TYPES,
    DEFAULT_RESPONSE_TYPES,
    MAX_AUTH_METHODS,
    MAX_CLIENT_NAME_LENGTH,
    MAX_GRANT_TYPES,
    MAX_REDIRECT_URIS,
    MAX_RESPONSE_TYPES,
    MAX_SCOPE_TOKENS,
    MAX_SHORT_STRING_LENGTH,
    MAX_URI_LENGTH,
    SHARED_SECRET_AUTH_METHODS,
    SIGNING_ALGS,
)
from authentik.enterprise.providers.oauth2_cimd.errors import InvalidClientID, InvalidClientMetadata
from authentik.enterprise.providers.oauth2_cimd.jwks import ClientKeySet, validate_jwks
from authentik.lib.utils.untrusted_fetch import InvalidURL, parse_untrusted_url

# Fields that would carry a shared secret (draft -03 section 4.1)
SECRET_FIELDS = frozenset(("client_secret", "client_secret_expires_at"))
# Fields through which a dynamically registered client manages its own local
# registration. A metadata document can never hold local authority, so they are rejected.
LOCAL_AUTHORITY_FIELDS = frozenset(("registration_access_token", "registration_client_uri"))
# Prefix reserved for local configuration; a document can't set authentik-specific values
LOCAL_FIELD_PREFIXES = ("authentik", "goauthentik")

# RFC 6749 section 3.3 scope-token
_SCOPE_TOKEN_RE = re.compile(r"^[\x21\x23-\x5b\x5d-\x7e]+$")
_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*$")
_BLOCKED_REDIRECT_SCHEMES = frozenset(("javascript", "data", "vbscript", "file", "blob", "about"))
_LOOPBACK_HOSTS = frozenset(("localhost",))


@dataclass(frozen=True)
class ClientMetadata:
    """A validated Client ID Metadata Document.

    Holds only the fields authentik understands. Unknown fields are never
    exposed, so they can't influence local configuration."""

    client_id: str
    client_name: str | None
    redirect_uris: tuple[str, ...]
    grant_types: tuple[str, ...]
    response_types: tuple[str, ...]
    # Declared token endpoint authentication methods, in document order. From
    # `token_endpoint_auth_methods_supported`, else the singular
    # `token_endpoint_auth_method`, else `none` (draft -03 section 5).
    token_endpoint_auth_methods: tuple[str, ...]
    token_endpoint_auth_signing_alg: str | None
    # Inline keys, if the document has `jwks`. Mutually exclusive with `jwks_uri`.
    jwks: ClientKeySet | None
    jwks_uri: str | None
    # Declared scopes. A restriction the client places on itself, never a grant.
    scopes: frozenset[str] | None
    client_uri: str | None
    logo_uri: str | None
    tos_uri: str | None
    policy_uri: str | None
    software_id: str | None
    software_version: str | None
    dpop_bound_access_tokens: bool

    @property
    def has_keys(self) -> bool:
        """True if the document declares key material (inline or by reference)"""
        return self.jwks is not None or self.jwks_uri is not None


def validate_client_id(client_id: Any) -> str:
    """Check that `client_id` is a client identifier URL we can fetch (draft -03 section 3).

    The fetcher's URL rules add local restrictions (no query, no percent-encoded
    separators). Raises InvalidClientID."""
    if not isinstance(client_id, str):
        raise InvalidClientID("invalid_client_id", "Client ID must be a string")
    try:
        parsed = parse_untrusted_url(client_id, MAX_URI_LENGTH)
    except InvalidURL as exc:
        raise InvalidClientID("invalid_client_id", "Client ID is not a valid URL") from exc
    if parsed.path == "/":
        raise InvalidClientID("invalid_client_id", "Client ID must have a path")
    return client_id


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


def _is_loopback(hostname: str) -> bool:
    if hostname in _LOOPBACK_HOSTS:
        return True
    try:
        return ip_address(hostname).is_loopback
    except ValueError:
        return False


def _validate_redirect_uri(uri: str) -> None:
    if not uri.isascii() or any(c <= " " or c == "\x7f" for c in uri):
        raise InvalidClientMetadata(
            "invalid_redirect_uri", "Redirect URI contains invalid characters"
        )
    try:
        parts = urlsplit(uri)
        parts.port  # noqa: B018 - validates the port
    except ValueError:
        raise InvalidClientMetadata("invalid_redirect_uri", "Redirect URI is malformed") from None
    scheme = parts.scheme.lower()
    if not _SCHEME_RE.match(scheme) or scheme in _BLOCKED_REDIRECT_SCHEMES:
        raise InvalidClientMetadata("invalid_redirect_uri", "Redirect URI scheme is not allowed")
    if parts.fragment or "#" in uri:
        raise InvalidClientMetadata("invalid_redirect_uri", "Redirect URI must not have a fragment")
    if scheme in ("http", "https"):
        if not parts.hostname or parts.username is not None or parts.password is not None:
            raise InvalidClientMetadata(
                "invalid_redirect_uri", "Redirect URI has an invalid authority"
            )
        # Plain HTTP only on the loopback interface (RFC 8252 section 7.3, RFC 9700)
        if scheme == "http" and not _is_loopback(parts.hostname):
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


def _auth_methods(doc: dict[str, Any]) -> tuple[str, ...]:
    plural = _str_list(doc, "token_endpoint_auth_methods_supported", MAX_AUTH_METHODS)
    singular = _str(doc, "token_endpoint_auth_method")
    if plural is not None:
        if not plural:
            raise InvalidClientMetadata(
                "invalid_value", "token_endpoint_auth_methods_supported must not be empty"
            )
        if singular is not None and singular not in plural:
            raise InvalidClientMetadata(
                "auth_method_conflict",
                "token_endpoint_auth_method is not in token_endpoint_auth_methods_supported",
            )
        methods = plural
    elif singular is not None:
        methods = (singular,)
    else:
        # Draft -03 section 5: default to `none`, never RFC 7591's `client_secret_basic`
        methods = (AUTH_METHOD_NONE,)
    if SHARED_SECRET_AUTH_METHODS.intersection(methods):
        raise InvalidClientMetadata("shared_secret", "Shared-secret authentication is not allowed")
    return methods


def _keys(doc: dict[str, Any]) -> tuple[ClientKeySet | None, str | None]:
    has_jwks = doc.get("jwks") is not None
    has_jwks_uri = doc.get("jwks_uri") is not None
    if has_jwks and has_jwks_uri:
        raise InvalidClientMetadata("jwks_conflict", "jwks and jwks_uri are mutually exclusive")
    if has_jwks:
        return validate_jwks(doc["jwks"]), None
    jwks_uri = _str(doc, "jwks_uri", MAX_URI_LENGTH)
    if jwks_uri is not None:
        try:
            parse_untrusted_url(jwks_uri, MAX_URI_LENGTH)
        except InvalidURL as exc:
            raise InvalidClientMetadata("invalid_jwks_uri", "jwks_uri is not acceptable") from exc
    return None, jwks_uri


def _scopes(doc: dict[str, Any]) -> frozenset[str] | None:
    scope = _str(doc, "scope", MAX_URI_LENGTH)
    if scope is None:
        return None
    tokens = scope.split(" ")
    if len(tokens) > MAX_SCOPE_TOKENS or not all(_SCOPE_TOKEN_RE.match(t) for t in tokens):
        raise InvalidClientMetadata("invalid_value", "scope is malformed")
    return frozenset(tokens)


def _check_prohibited(doc: dict[str, Any]) -> None:
    if SECRET_FIELDS & doc.keys():
        raise InvalidClientMetadata("shared_secret", "Document contains a client secret")
    if LOCAL_AUTHORITY_FIELDS & doc.keys() or any(
        name.lower().startswith(LOCAL_FIELD_PREFIXES) for name in doc
    ):
        raise InvalidClientMetadata("local_authority", "Document claims local configuration")


def validate_metadata(document: dict[str, Any], client_id: str) -> ClientMetadata:
    """Validate a parsed metadata document fetched from `client_id`.

    Raises InvalidClientMetadata (or InvalidClientKeys for inline keys)."""
    if document.get("client_id") != client_id:
        # Simple string comparison, no normalization (draft -03 section 3)
        raise InvalidClientMetadata("client_id_mismatch", "client_id does not match the URL")
    _check_prohibited(document)
    redirect_uris = _str_list(document, "redirect_uris", MAX_REDIRECT_URIS, MAX_URI_LENGTH) or ()
    for uri in redirect_uris:
        _validate_redirect_uri(uri)
    grant_types = _str_list(document, "grant_types", MAX_GRANT_TYPES)
    response_types = _str_list(document, "response_types", MAX_RESPONSE_TYPES)
    signing_alg = _str(document, "token_endpoint_auth_signing_alg")
    if signing_alg is not None and signing_alg not in SIGNING_ALGS:
        raise InvalidClientMetadata(
            "unsupported_alg", "token_endpoint_auth_signing_alg is not an allowed algorithm"
        )
    dpop_bound = document.get("dpop_bound_access_tokens", False)
    if not isinstance(dpop_bound, bool):
        raise InvalidClientMetadata("invalid_type", "dpop_bound_access_tokens must be a boolean")
    jwks, jwks_uri = _keys(document)
    return ClientMetadata(
        client_id=client_id,
        client_name=_str(document, "client_name", MAX_CLIENT_NAME_LENGTH),
        redirect_uris=redirect_uris,
        grant_types=DEFAULT_GRANT_TYPES if grant_types is None else grant_types,
        response_types=DEFAULT_RESPONSE_TYPES if response_types is None else response_types,
        token_endpoint_auth_methods=_auth_methods(document),
        token_endpoint_auth_signing_alg=signing_alg,
        jwks=jwks,
        jwks_uri=jwks_uri,
        scopes=_scopes(document),
        client_uri=_informative_uri(document, "client_uri"),
        logo_uri=_informative_uri(document, "logo_uri"),
        tos_uri=_informative_uri(document, "tos_uri"),
        policy_uri=_informative_uri(document, "policy_uri"),
        software_id=_str(document, "software_id"),
        software_version=_str(document, "software_version"),
        dpop_bound_access_tokens=dpop_bound,
    )
