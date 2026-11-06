"""OAuth client context and resolution

Protocol endpoints identify the calling client by ``client_id``. Historically that
identifier was used directly to look up the ``OAuth2Provider``, which conflates two
concerns: selecting the provider (the authorization-server boundary: issuer, signing,
flows, policies), and resolving the client making the request within that provider.

This module separates them:

- A ``ProviderSelector`` picks the ``OAuth2Provider`` that handles a request.
- A ``ClientAdapter`` resolves an ``OAuthClientContext`` within that provider.
- ``OAuthClientResolver`` combines a selector with an ordered list of adapters.

Core only knows the legacy registration kind: every registered ``OAuth2Provider`` is
its own client. Other registration kinds are supplied by components outside core,
which add their own selectors and adapters, and subclass ``OAuthClientContext`` to
carry their own client attributes. Legacy resolution never fetches anything from the
network; a registered ``client_id`` that happens to be an HTTPS URL is a static client.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from hmac import compare_digest
from typing import TYPE_CHECKING

from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.providers.oauth2.models import (
    ClientGrantBinding,
    ClientType,
    OAuth2Provider,
    RedirectURI,
)

if TYPE_CHECKING:
    from authentik.core.models import Application

LOGGER = get_logger()


class ClientRegistrationKind(StrEnum):
    """How core knows a client. Components that add other registration kinds define
    their own values; ``OAuthClientContext.registration_kind`` accepts any string."""

    # A registered OAuth2Provider, identified by its own client_id
    LEGACY = "legacy"


class ClientAuthMethod(StrEnum):
    """Token endpoint authentication methods (RFC 7591 section 2) known to core.
    ``OAuthClientContext.token_endpoint_auth_method`` accepts any string."""

    NONE = "none"
    CLIENT_SECRET_BASIC = "client_secret_basic"
    CLIENT_SECRET_POST = "client_secret_post"


@dataclass(frozen=True, slots=True)
class OAuthClientContext:
    """Immutable description of the client making an OAuth request.

    ``provider`` remains the local security boundary (issuer, signing keys, flows,
    property mappings and policies). Everything that identifies or describes the
    *client* is read from this context instead of from the provider, so that clients
    which are not themselves providers can be supported. Subclasses may add fields;
    they must stay frozen, slotted and picklable, as contexts are stored in flow plans."""

    provider: OAuth2Provider
    # Exact client identifier as presented by the client; never normalized
    client_id: str
    # A ``ClientRegistrationKind`` for core clients
    registration_kind: str
    client_type: ClientType
    # Validated redirect URIs for the authorization endpoint
    redirect_uris: tuple[RedirectURI, ...]
    # Effective grant types this client may use
    grant_types: frozenset[str]

    @property
    def application(self) -> Application | None:
        """Application the provider is assigned to, if any"""
        from authentik.core.models import Application

        try:
            return self.provider.application
        except Application.DoesNotExist:
            return None

    @property
    def is_legacy(self) -> bool:
        return self.registration_kind == ClientRegistrationKind.LEGACY

    @property
    def is_registered_client(self) -> bool:
        """Whether this is the client registered on the provider itself. Grants issued
        before grants recorded their client belong to this client only."""
        return self.is_legacy and self.client_id == self.provider.client_id

    @property
    def is_confidential(self) -> bool:
        return self.client_type == ClientType.CONFIDENTIAL

    @property
    def token_endpoint_auth_method(self) -> str:
        """Authentication method selected for this client at the token endpoint.

        Registered confidential clients may send their secret either way; they are
        recorded with the RFC 7591 default, ``client_secret_basic``."""
        if self.is_confidential:
            return ClientAuthMethod.CLIENT_SECRET_BASIC
        return ClientAuthMethod.NONE

    @property
    def grant_binding(self) -> ClientGrantBinding:
        """Client attributes recorded on grants issued to this client. Subclasses which
        reference a credential managed elsewhere add it as an external binding."""
        return ClientGrantBinding(
            client_id=self.client_id,
            auth_method=self.token_endpoint_auth_method,
        )

    def matches_grant_binding(self, binding: ClientGrantBinding) -> bool:
        """Check whether a grant recorded with ``binding`` may be used by this client.

        The exact client identifier and any external binding must always match. The
        authentication method is compared for every registration kind except legacy:
        a registered client's authentication requirements follow its provider's current
        configuration, which is checked on every request, as it always has been."""
        expected = self.grant_binding
        if binding.client_id != expected.client_id:
            return False
        if (
            binding.external_binding != expected.external_binding
            or binding.external_binding_version != expected.external_binding_version
        ):
            return False
        if self.is_legacy:
            return True
        return binding.auth_method == expected.auth_method

    def check_client_secret(self, client_secret: str) -> bool:
        """Check a shared client secret. Only legacy clients have shared secrets;
        subclasses for other registration kinds authenticate clients differently."""
        if not self.is_legacy:
            return False
        return compare_digest(self.provider.client_secret, client_secret)

    @staticmethod
    def for_provider(provider: OAuth2Provider) -> OAuthClientContext:
        """Build the context for a registered OAuth2Provider, which is its own client"""
        return OAuthClientContext(
            provider=provider,
            client_id=provider.client_id,
            registration_kind=ClientRegistrationKind.LEGACY,
            client_type=ClientType(provider.client_type),
            redirect_uris=tuple(provider.authorization_redirect_uris),
            grant_types=frozenset(provider.grant_types),
        )


class ProviderSelector:
    """Select the provider responsible for a request"""

    def select(self, request: HttpRequest | None, client_id: str) -> OAuth2Provider | None:
        raise NotImplementedError


class LegacyProviderSelector(ProviderSelector):
    """Select the provider whose registered client_id matches the request's client_id.

    This is how the shared (non provider-scoped) endpoints have always worked; it can
    only ever select a provider that registered this exact client_id."""

    def __init__(self, provider_class: type[OAuth2Provider] = OAuth2Provider):
        self.provider_class = provider_class

    def select(self, request: HttpRequest | None, client_id: str) -> OAuth2Provider | None:
        return self.provider_class.objects.filter(client_id=client_id).first()


class ClientAdapter:
    """Resolve a client within an already selected provider"""

    def resolve(
        self, request: HttpRequest | None, provider: OAuth2Provider, client_id: str
    ) -> OAuthClientContext | None:
        raise NotImplementedError


class LegacyClientAdapter(ClientAdapter):
    """Resolve the client registered directly on the provider"""

    def resolve(
        self, request: HttpRequest | None, provider: OAuth2Provider, client_id: str
    ) -> OAuthClientContext | None:
        if provider.client_id != client_id:
            return None
        return OAuthClientContext.for_provider(provider)


class OAuthClientResolver:
    """Select a provider and resolve the client context within it.

    Adapters are tried in order and the first match wins. A provider's registered
    client always comes first, so that a registered client_id keeps its static meaning
    even when it is shaped like a URL."""

    def __init__(
        self,
        selector: ProviderSelector,
        adapters: Sequence[ClientAdapter] | None = None,
    ):
        self.selector = selector
        self.adapters: tuple[ClientAdapter, ...] = tuple(
            adapters if adapters is not None else [LegacyClientAdapter()]
        )

    def resolve(self, request: HttpRequest | None, client_id: str) -> OAuthClientContext | None:
        provider = self.selector.select(request, client_id)
        if not provider:
            LOGGER.debug("No provider selected for client", client_id=client_id)
            return None
        for adapter in self.adapters:
            client = adapter.resolve(request, provider, client_id)
            if client:
                return client
        LOGGER.debug("No client resolved within provider", client_id=client_id, provider=provider)
        return None

    @staticmethod
    def legacy(provider_class: type[OAuth2Provider] = OAuth2Provider) -> OAuthClientResolver:
        """Resolver for the shared endpoints, which only know registered clients"""
        return OAuthClientResolver(LegacyProviderSelector(provider_class), [LegacyClientAdapter()])
