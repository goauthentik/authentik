"""The resolved public CIMD client"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CIMDClient:
    """A public client resolved from its Client ID Metadata Document.

    Built only from primitives so it can be pickled into flow plans. Holds no
    keys and no raw document. Every value is self-declared by the client and
    can only narrow what the provider allows, never widen it."""

    client_id: str
    # The document's `client_name`, or the client ID's host when it has none
    client_name: str
    # False when `client_name` is the client ID's host fallback
    client_name_declared: bool
    # Display-only HTTPS URLs; anything else the document declares is dropped
    client_uri: str | None
    policy_uri: str | None
    tos_uri: str | None
    # Registered redirect URIs, validated. Match with `redirect_uri_allowed()`.
    redirect_uris: tuple[str, ...]
    # A non-empty subset of (authorization_code, refresh_token); always has authorization_code
    grant_types: tuple[str, ...]
    # Always "none": public clients don't authenticate at the token endpoint
    token_endpoint_auth_method: str
    # The document's `scope`: a restriction the client places on itself, never
    # a grant. None when the document declares no scope.
    scopes: tuple[str, ...] | None
    # Wall-clock time (epoch seconds) until which this result may be used
    # without resolving again
    expires_at: float
    # True when the document's freshness has passed and refetching it failed
    # transiently, so the last valid document is used (draft -03 section 6.1)
    stale: bool
