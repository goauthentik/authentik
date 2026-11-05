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

How a client authenticates is part of its context too: ``token_endpoint_auth_method``
and ``authenticate``. Callers resolve the client first and let it authenticate the
presented credentials, so the method is decided by the client's registration, never by
which parameters a request happens to carry.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from hmac import compare_digest
from typing import TYPE_CHECKING

from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.providers.oauth2.client_auth import (
    ClientAuthentication,
    ClientAuthenticationError,
    ClientAuthMethod,
    PresentedClientCredentials,
)
from authentik.providers.oauth2.models import ClientType, OAuth2Provider, RedirectURI

if TYPE_CHECKING:
    from authentik.core.models import Application

LOGGER = get_logger()


class ClientRegistrationKind(StrEnum):
    """How core knows a client. Components that add other registration kinds define
    their own values; ``OAuthClientContext.registration_kind`` accepts any string."""

    # A registered OAuth2Provider, identified by its own client_id
    LEGACY = "legacy"


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
    def is_confidential(self) -> bool:
        return self.client_type == ClientType.CONFIDENTIAL

    def check_client_secret(self, client_secret: str) -> bool:
        """Check a shared client secret. Only legacy clients have shared secrets, so this
        always returns False for other registration kinds: their subclasses authenticate
        clients by overriding ``token_endpoint_auth_method`` and ``authenticate`` (for
        example with ``private_key_jwt``), and a confidential client of a kind that
        doesn't is unauthenticatable."""
        if not self.is_legacy:
            return False
        return compare_digest(self.provider.client_secret, client_secret)

    @property
    def token_endpoint_auth_method(self) -> ClientAuthMethod:
        """How this client authenticates (RFC 7591 ``token_endpoint_auth_method``).

        Confidential legacy clients report ``client_secret_basic``, RFC 7591's default,
        and accept ``client_secret_post`` as well, as they always have. Public clients
        report ``none``. Subclasses for other registration kinds override this together
        with ``authenticate``."""
        if self.is_confidential:
            return ClientAuthMethod.CLIENT_SECRET_BASIC
        return ClientAuthMethod.NONE

    def authenticate(
        self, request: HttpRequest | None, credentials: PresentedClientCredentials
    ) -> ClientAuthentication:
        """Authenticate this client with the ``credentials`` presented in ``request``.
        Raises ``ClientAuthenticationError``.

        Called once the client was resolved from ``credentials.client_id``. The client
        decides how it authenticates; presenting different credentials never selects
        another method. Subclasses for other registration kinds override this together
        with ``token_endpoint_auth_method``.

        Legacy clients behave as the token endpoint always has: a confidential client
        presents its shared secret (Basic or POST), checked with
        ``check_client_secret``; a public client is not authenticated, and anything it
        presents is ignored. A client assertion never authenticates a confidential
        legacy client. (The ``client_assertion`` of the ``client_credentials`` grant is
        a federated *user* JWT handled by that grant, not client authentication.)"""
        from authentik.providers.oauth2.utils import is_all_vschar

        if credentials.client_id != self.client_id:
            raise ClientAuthenticationError("client_id_mismatch")
        if not self.is_confidential:
            return ClientAuthentication(client=self, method=ClientAuthMethod.NONE)
        if credentials.method == ClientAuthMethod.PRIVATE_KEY_JWT:
            raise ClientAuthenticationError("auth_method_not_allowed")
        secret = credentials.client_secret
        if (
            credentials.method
            not in (ClientAuthMethod.CLIENT_SECRET_BASIC, ClientAuthMethod.CLIENT_SECRET_POST)
            or secret is None
            or not is_all_vschar(secret)
            or not self.check_client_secret(secret)
        ):
            raise ClientAuthenticationError("invalid_secret")
        return ClientAuthentication(client=self, method=ClientAuthMethod(credentials.method))

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
