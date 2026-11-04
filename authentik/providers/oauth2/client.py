"""OAuth client context: the client a request acts as, and the provider governing it"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from authentik.providers.oauth2.models import OAuth2Provider


class ClientRegistrationKind(StrEnum):
    """How authentik knows a client"""

    # Registered as an OAuth2Provider and identified by its client ID
    LEGACY = "legacy"
    # PROTOTYPE (01b): identified by a Client ID Metadata Document URL
    METADATA = "metadata"


@dataclass(frozen=True, slots=True)
class OAuthClientContext:
    """The OAuth client a request acts as.

    `provider` remains the local security boundary: application, issuer, signing key,
    flows and policies. `client_id` is the exact identifier the client presented.
    For legacy clients the two are the same registration, but later client kinds
    are resolved within a provider without being providers themselves."""

    provider: OAuth2Provider
    client_id: str
    registration_kind: ClientRegistrationKind
    # PROTOTYPE (01b): values taken from a fetched client metadata document
    redirect_uris: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def for_provider(provider: OAuth2Provider) -> OAuthClientContext:
        """Context for a client registered as `provider`"""
        return OAuthClientContext(
            provider=provider,
            client_id=provider.client_id,
            registration_kind=ClientRegistrationKind.LEGACY,
        )


class ClientSelector:
    """Resolve the client named by a request's `client_id`"""

    def resolve(self, client_id: str) -> OAuthClientContext | None:
        """Return the client's context, or None when the client is unknown"""
        raise NotImplementedError


class LegacyClientSelector(ClientSelector):
    """Resolve registered clients, where the client ID identifies the provider.

    Matches the exact registered client ID only. The shape of a client ID never causes
    a lookup elsewhere, so a registered ID that is an HTTPS URL stays a static client."""

    def resolve(self, client_id: str) -> OAuthClientContext | None:
        provider = OAuth2Provider.objects.filter(client_id=client_id).first()
        if not provider:
            return None
        return OAuthClientContext.for_provider(provider)
