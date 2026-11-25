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

``OAuthClientContext`` also carries the per-client policy hooks the protocol endpoints
consult: redirect URI matching, PKCE requirements, the authorization flow, resource
indicators and refresh token rotation. Their defaults read the provider's configuration,
so registered clients behave exactly as they always have; subclasses override them.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from hmac import compare_digest
from re import error as RegexError
from re import fullmatch
from typing import TYPE_CHECKING

from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.models import (
    ClientGrantBinding,
    ClientType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)

if TYPE_CHECKING:
    from authentik.core.models import Application
    from authentik.flows.models import Flow
    from authentik.providers.oauth2.models import RefreshToken

# Called with a configured regular expression redirect URI that failed to compile
InvalidRedirectURIPatternHandler = Callable[[RedirectURI, RegexError], None]

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
    # Whether an authorization code may only be issued and redeemed with PKCE (RFC 7636)
    pkce_required: bool = field(default=False, kw_only=True)
    # Code challenge methods this client may use. None allows every method core supports;
    # a set is enforced at the authorization endpoint and again when redeeming the code,
    # so a code issued with another method can never be redeemed.
    pkce_methods: frozenset[str] | None = field(default=None, kw_only=True)

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
    def display_name(self) -> str | None:
        """Name the client presents for itself, shown to users next to its identifier.
        Registered clients have none; they are presented by their application."""
        return None

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

    def allows_redirect_uri(
        self,
        redirect_uri: str,
        on_invalid_pattern: InvalidRedirectURIPatternHandler | None = None,
    ) -> bool:
        """Check whether the authorization endpoint may redirect to `redirect_uri` for this
        client. By default, it must match one of `redirect_uris`, exactly or by regular
        expression. Regular expressions which fail to compile are reported to
        `on_invalid_pattern`, or logged when none is given, and never match.

        The token endpoint checks registered clients against their redirect URIs again;
        other clients must redeem a code with the exact redirect URI it was issued for."""
        for allowed in self.redirect_uris:
            if allowed.matching_mode == RedirectURIMatchingMode.STRICT:
                if redirect_uri == allowed.url:
                    return True
            if allowed.matching_mode == RedirectURIMatchingMode.REGEX:
                try:
                    if fullmatch(allowed.url, redirect_uri):
                        return True
                except RegexError as exc:
                    if on_invalid_pattern:
                        on_invalid_pattern(allowed, exc)
                    else:
                        LOGGER.warning(
                            "Failed to parse regular expression",
                            exc=exc,
                            url=allowed.url,
                            provider=self.provider,
                        )
        return False

    @property
    def authorization_flow(self) -> Flow | None:
        """Flow users authorize this client with, by default the provider's"""
        return self.provider.authorization_flow

    def allowed_resources(self) -> frozenset[str]:
        """Resources (RFC 8707) this client may request tokens for, by default the ones
        configured on its provider. Empty when resource indicators are not supported, in
        which case the ``resource`` parameter is ignored."""
        return frozenset(self.provider.allowed_resources)

    def default_resources(self) -> tuple[str, ...]:
        """Resources a new grant is restricted to when the request names none. They must
        be allowed. By default none, so that such grants are not restricted."""
        return ()

    @property
    def requires_single_resource(self) -> bool:
        """Whether every grant of this client must be restricted to exactly one resource,
        so that its access tokens always have a resource as their audience, never the
        client. False by default."""
        return False

    def rotates_refresh_tokens(self, refresh_token: RefreshToken, now: datetime) -> bool:
        """Whether refreshing with `refresh_token` at `now` issues a new refresh token and
        revokes `refresh_token`. By default, refresh tokens rotate when the provider's
        refresh token threshold is zero, or once less than the threshold remains."""
        threshold = timedelta_from_string(self.provider.refresh_token_threshold)
        return threshold.total_seconds() == 0 or (refresh_token.expires - now) < threshold

    @property
    def grant_binding(self) -> ClientGrantBinding:
        """Client attributes recorded on grants issued to this client"""
        return ClientGrantBinding(
            client_id=self.client_id,
            auth_method=self.token_endpoint_auth_method,
        )

    def matches_grant_binding(self, binding: ClientGrantBinding) -> bool:
        """Check whether a grant recorded with ``binding`` may be used by this client.

        The exact client identifier must always match. The
        authentication method is compared for every registration kind except legacy:
        a registered client's authentication requirements follow its provider's current
        configuration, which is checked on every request, as it always has been."""
        expected = self.grant_binding
        if binding.client_id != expected.client_id:
            return False
        if self.is_legacy:
            return True
        return binding.auth_method == expected.auth_method

    def check_client_secret(self, client_secret: str) -> bool:
        """Check a shared client secret. Only legacy clients have shared secrets;
        subclasses for other registration kinds authenticate clients differently.

        Non-legacy confidential clients are intentionally unauthenticatable (this always
        returns False) until a subclass overrides this method; that arrives in
        `cimd/11-private-key-jwt`."""
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
        return self.resolve_in_provider(request, provider, client_id)

    def resolve_in_provider(
        self, request: HttpRequest | None, provider: OAuth2Provider, client_id: str
    ) -> OAuthClientContext | None:
        """Resolve a client within a provider that is already known, for example the
        provider of a grant, without selecting one"""
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
