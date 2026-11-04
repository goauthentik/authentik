"""OAuth client context and resolution

Protocol endpoints identify the calling client by ``client_id``. Historically that
identifier was used directly to look up the ``OAuth2Provider``, which conflates two
concerns: selecting the provider (the authorization-server boundary: issuer, signing,
flows, policies), and resolving the client making the request within that provider.

This module separates them:

- A ``ProviderSelector`` picks the ``OAuth2Provider`` that handles a request.
- A ``ClientAdapter`` resolves an ``OAuthClientContext`` within that provider.
- ``OAuthClientResolver`` combines a selector with an ordered list of adapters.

Only the legacy registration kind exists at the moment: every registered
``OAuth2Provider`` is its own client. Resolution never fetches anything from the
network; a registered ``client_id`` that happens to be an HTTPS URL is still a
static client.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from hmac import compare_digest
from typing import TYPE_CHECKING

from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.providers.oauth2.models import ClientType, OAuth2Provider, RedirectURI

if TYPE_CHECKING:
    from authentik.core.models import Application

LOGGER = get_logger()

TOKEN_ENDPOINT_AUTH_CLIENT_SECRET_BASIC = "client_secret_basic"
TOKEN_ENDPOINT_AUTH_CLIENT_SECRET_POST = "client_secret_post"
TOKEN_ENDPOINT_AUTH_NONE = "none"


class ClientRegistrationKind(StrEnum):
    """How a client is known to authentik"""

    # A registered OAuth2Provider, identified by its own client_id
    LEGACY = "legacy"
    # A client admitted by provider configuration and described by a metadata document
    ADMITTED_METADATA = "admitted_metadata"
    # An explicitly onboarded client described by a metadata document
    MANAGED_METADATA = "managed_metadata"


@dataclass(frozen=True, slots=True)
class OAuthClientContext:
    """Immutable description of the client making an OAuth request.

    ``provider`` remains the local security boundary (issuer, signing keys, flows,
    property mappings and policies). Everything that identifies or describes the
    *client* is read from this context instead of from the provider, so that clients
    which are not themselves providers can be supported later."""

    provider: OAuth2Provider
    # Exact client identifier as presented by the client; never normalized
    client_id: str
    registration_kind: ClientRegistrationKind
    client_name: str
    client_type: ClientType
    # Validated redirect URIs for the authorization endpoint
    redirect_uris: tuple[RedirectURI, ...]
    # Token endpoint authentication methods this client may use
    token_endpoint_auth_methods: frozenset[str]
    # Effective grant types this client may use
    grant_types: frozenset[str]
    # Effective response types, ``None`` when only restricted by ``grant_types``
    response_types: frozenset[str] | None = None
    # Effective scopes, ``None`` when only restricted by the provider's scope mappings
    allowed_scopes: frozenset[str] | None = None
    # Resources (RFC 8707) this client may request tokens for
    resources: tuple[str, ...] = ()
    # Validated public keys of the client, when it has any
    jwks: dict | None = None
    # Local admission entry or managed credential, when applicable
    admission_id: str | None = None
    configuration_version: int | None = None
    # Opaque binding to a managed agent, only set for managed credentials
    agent_binding: str | None = None

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
        """Check a shared client secret. Only legacy clients have shared secrets."""
        if not self.is_legacy:
            return False
        return compare_digest(self.provider.client_secret, client_secret)

    @staticmethod
    def for_provider(provider: OAuth2Provider) -> OAuthClientContext:
        """Build the context for a registered OAuth2Provider, which is its own client"""
        if provider.client_type == ClientType.CONFIDENTIAL:
            auth_methods = frozenset(
                [TOKEN_ENDPOINT_AUTH_CLIENT_SECRET_BASIC, TOKEN_ENDPOINT_AUTH_CLIENT_SECRET_POST]
            )
        else:
            auth_methods = frozenset([TOKEN_ENDPOINT_AUTH_NONE])
        return OAuthClientContext(
            provider=provider,
            client_id=provider.client_id,
            registration_kind=ClientRegistrationKind.LEGACY,
            client_name=provider.name,
            client_type=ClientType(provider.client_type),
            redirect_uris=tuple(provider.authorization_redirect_uris),
            token_endpoint_auth_methods=auth_methods,
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
