"""Effective-capability negotiation between a client's metadata and a local profile"""

from dataclasses import dataclass, replace
from enum import StrEnum

from authentik.enterprise.providers.oauth2_cimd.constants import (
    AUTH_METHOD_NONE,
    AUTH_METHOD_PRIVATE_KEY_JWT,
    GRANT_AUTHORIZATION_CODE,
    GRANT_DEVICE_CODE,
    GRANT_JWT_BEARER,
    GRANT_REFRESH_TOKEN,
    GRANT_TOKEN_EXCHANGE,
    PKCE_METHOD_S256,
    RESPONSE_TYPE_CODE,
)
from authentik.enterprise.providers.oauth2_cimd.errors import UnsupportedClient
from authentik.enterprise.providers.oauth2_cimd.jwks import ClientKeySet
from authentik.enterprise.providers.oauth2_cimd.metadata import ClientMetadata


class ProfileName(StrEnum):
    """Locally required client profile"""

    PUBLIC = "public"
    MANAGED = "managed"


@dataclass(frozen=True)
class ClientProfile:
    """What authentik locally allows for a class of CIMD clients.

    The document can only narrow this, never widen it. Use `restrict()` to
    narrow a profile further, for example to the grants a provider enables."""

    name: ProfileName
    # Acceptable token endpoint authentication methods, in order of preference
    auth_methods: tuple[str, ...]
    grant_types: frozenset[str]
    response_types: frozenset[str]
    # Grants that must remain after intersection
    required_grant_types: frozenset[str]
    requires_signing_keys: bool

    def restrict(
        self,
        *,
        grant_types: frozenset[str] | None = None,
        response_types: frozenset[str] | None = None,
    ) -> ClientProfile:
        """A copy of this profile limited to the given values (intersection only)"""
        return replace(
            self,
            grant_types=(
                self.grant_types & grant_types if grant_types is not None else self.grant_types
            ),
            response_types=(
                self.response_types & response_types
                if response_types is not None
                else self.response_types
            ),
        )


PUBLIC_PROFILE = ClientProfile(
    name=ProfileName.PUBLIC,
    auth_methods=(AUTH_METHOD_NONE,),
    grant_types=frozenset((GRANT_AUTHORIZATION_CODE, GRANT_REFRESH_TOKEN)),
    response_types=frozenset((RESPONSE_TYPE_CODE,)),
    required_grant_types=frozenset((GRANT_AUTHORIZATION_CODE,)),
    requires_signing_keys=False,
)

MANAGED_PROFILE = ClientProfile(
    name=ProfileName.MANAGED,
    auth_methods=(AUTH_METHOD_PRIVATE_KEY_JWT,),
    grant_types=frozenset(
        (
            GRANT_AUTHORIZATION_CODE,
            GRANT_REFRESH_TOKEN,
            GRANT_DEVICE_CODE,
            GRANT_TOKEN_EXCHANGE,
            GRANT_JWT_BEARER,
        )
    ),
    response_types=frozenset((RESPONSE_TYPE_CODE,)),
    required_grant_types=frozenset(),
    requires_signing_keys=True,
)


@dataclass(frozen=True)
class EffectiveCapabilities:
    """What a client may actually use"""

    profile: ProfileName
    token_endpoint_auth_method: str
    grant_types: frozenset[str]
    response_types: frozenset[str]
    redirect_uris: tuple[str, ...]
    # Authorization code requests must use PKCE with one of these methods
    pkce_required: bool
    pkce_methods: frozenset[str]

    @property
    def confidential(self) -> bool:
        """True if the client authenticates at the token endpoint"""
        return self.token_endpoint_auth_method != AUTH_METHOD_NONE


def negotiate(
    metadata: ClientMetadata,
    profile: ClientProfile,
    keys: ClientKeySet | None = None,
) -> EffectiveCapabilities:
    """Compute effective capabilities (draft -03 sections 5 and 6).

    `keys` are the client's validated signing keys, required for profiles that
    authenticate with keys. Raises UnsupportedClient."""
    method = next(
        (m for m in profile.auth_methods if m in metadata.token_endpoint_auth_methods), None
    )
    if method is None:
        # A document declaring `none` can't bypass a locally required method
        raise UnsupportedClient(
            "auth_method_unsupported", "No supported token endpoint authentication method"
        )
    if profile.requires_signing_keys or method == AUTH_METHOD_PRIVATE_KEY_JWT:
        if not metadata.has_keys:
            raise UnsupportedClient("signing_keys_required", "Client declares no signing keys")
        if not keys:
            raise UnsupportedClient("signing_keys_required", "Client has no usable signing keys")
    # Unsupported grant and response types are dropped
    grant_types = frozenset(metadata.grant_types) & profile.grant_types
    response_types = frozenset(metadata.response_types) & profile.response_types
    if not grant_types or not response_types:
        raise UnsupportedClient("no_common_grant", "No supported grant or response type")
    if not profile.required_grant_types <= grant_types:
        raise UnsupportedClient("required_grant_missing", "A required grant type is not declared")
    authorization_code = GRANT_AUTHORIZATION_CODE in grant_types
    if authorization_code and not metadata.redirect_uris:
        raise UnsupportedClient(
            "redirect_uris_required", "Authorization code requires redirect URIs"
        )
    if authorization_code and RESPONSE_TYPE_CODE not in response_types:
        raise UnsupportedClient("no_common_grant", "Authorization code requires response type code")
    return EffectiveCapabilities(
        profile=profile.name,
        token_endpoint_auth_method=method,
        grant_types=grant_types,
        response_types=response_types,
        redirect_uris=metadata.redirect_uris if authorization_code else (),
        pkce_required=authorization_code,
        pkce_methods=frozenset((PKCE_METHOD_S256,)),
    )
