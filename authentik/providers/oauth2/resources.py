"""Resource indicators (RFC 8707)

Clients name the protected resources they want an access token for with the ``resource``
parameter of authorization, device authorization and token requests. Access tokens issued
for one or more resources are audience-restricted to them, instead of to the client.

A provider supports resource indicators once any resources are allowed for it. The allowed
resources of a request are collected from ``ResourceSource``s:

- Core only knows the resources configured on the provider itself.
- Components outside core either register a source with ``register_resource_source()``,
  which then applies to every request, or override ``get_resource_resolver()`` on the
  protocol views they serve, which then applies to those views only.

A provider without any allowed resources ignores the ``resource`` parameter, as it always has.
Clients may send it to any authorization server whether or not it supports it, and MCP clients
send it on every authorization and token request.

Resources are compared as exact strings, without normalization, so that a client can never
obtain a token for a resource other than one that was allowed.
"""

from collections.abc import Iterable, Sequence
from re import compile as re_compile
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.providers.oauth2.models import GRANT_RESOURCE_MAX_LENGTH, join_resources

if TYPE_CHECKING:
    from authentik.providers.oauth2.client import OAuthClientContext

LOGGER = get_logger()

# Request parameter carrying a resource indicator, which may be repeated
RESOURCE_PARAM = "resource"

# Printable ASCII without space, the only characters a URI may contain
_PRINTABLE_ASCII = re_compile(r"[\x21-\x7e]+")
# URI scheme, RFC 3986 section 3.1
_SCHEME = re_compile(r"[A-Za-z][A-Za-z0-9+.-]*")


class ResourceIndicatorError(Exception):
    """A requested resource cannot be issued for. Reported to clients as `invalid_target`."""

    def __init__(self, cause: str):
        super().__init__(cause)
        self.cause = cause


def validate_resource_indicator(value: str) -> str:
    """Check that `value` is an absolute URI without a fragment (RFC 8707 section 2).

    Raises ValueError otherwise. Only printable ASCII is accepted, as a URI has no other
    characters, which also guarantees that a resource never contains a space."""
    if not _PRINTABLE_ASCII.fullmatch(value):
        raise ValueError("Resource must be a URI without whitespace or non-ASCII characters")
    if "#" in value:
        raise ValueError("Resource must not include a fragment")
    scheme, separator, _ = value.partition(":")
    if not separator or not _SCHEME.fullmatch(scheme):
        raise ValueError("Resource must be an absolute URI")
    if scheme.lower() in ("http", "https") and not urlsplit(value).hostname:
        raise ValueError("Resource must include a host")
    return value


def parse_resource_indicators(values: Iterable[str]) -> tuple[str, ...]:
    """Validate requested resources, dropping duplicates while keeping their order.
    Raises ResourceIndicatorError when any of them is not a valid resource indicator."""
    resources: dict[str, None] = {}
    for value in values:
        try:
            resources[validate_resource_indicator(value)] = None
        except ValueError as exc:
            LOGGER.info("Invalid resource indicator", resource=value, reason=str(exc))
            raise ResourceIndicatorError("resource_invalid") from None
    return tuple(resources)


class ResourceSource:
    """Contribute resources a client may request access tokens for"""

    def allowed_resources(
        self, request: HttpRequest | None, client: OAuthClientContext
    ) -> Iterable[str]:
        raise NotImplementedError


class ProviderResourceSource(ResourceSource):
    """Resources configured on the client's provider"""

    def allowed_resources(
        self, request: HttpRequest | None, client: OAuthClientContext
    ) -> Iterable[str]:
        return client.provider.allowed_resources


_registered_sources: list[ResourceSource] = []


def register_resource_source(source: ResourceSource) -> None:
    """Add a source consulted by the default resolver of every protocol view, for example
    from the `ready()` of the app that contributes resources. Sources must decide for
    themselves whether they apply to a request."""
    if source not in _registered_sources:
        _registered_sources.append(source)


def unregister_resource_source(source: ResourceSource) -> None:
    if source in _registered_sources:
        _registered_sources.remove(source)


def registered_resource_sources() -> tuple[ResourceSource, ...]:
    return tuple(_registered_sources)


class OAuthResourceResolver:
    """Decide which resources an access token is issued for"""

    def __init__(self, sources: Sequence[ResourceSource] | None = None):
        self.sources: tuple[ResourceSource, ...] = tuple(
            sources
            if sources is not None
            else (ProviderResourceSource(), *registered_resource_sources())
        )

    def allowed(self, request: HttpRequest | None, client: OAuthClientContext) -> frozenset[str]:
        """All resources `client` may request tokens for. Empty when the client's provider
        does not support resource indicators."""
        allowed: set[str] = set()
        for source in self.sources:
            allowed.update(source.allowed_resources(request, client))
        return frozenset(allowed)

    def resolve(
        self,
        request: HttpRequest | None,
        client: OAuthClientContext,
        requested: Sequence[str],
        granted: Sequence[str] = (),
    ) -> tuple[str, ...]:
        """Resources to issue for, given the `requested` resources of a request made with a
        grant restricted to the `granted` ones. A grant without resources is not restricted
        to any; its resources are limited by what is allowed only.

        Without any requested resources, or when the provider does not support resource
        indicators, the grant's resources are kept, so that a token is never issued for
        more than its grant. Otherwise, every requested resource must be allowed and be
        part of the grant; the result may only narrow the grant, never widen it.

        Raises ResourceIndicatorError when the requested resources can't be issued for."""
        granted = tuple(granted)
        if not requested:
            return granted
        # Only collected once resources are requested, as sources may query the database
        allowed = self.allowed(request, client)
        if not allowed:
            LOGGER.debug(
                "Ignoring resource indicators, no resources are allowed for the provider",
                client_id=client.client_id,
            )
            return granted
        resources = parse_resource_indicators(requested)
        if not allowed.issuperset(resources):
            LOGGER.info(
                "Requested resource is not allowed",
                client_id=client.client_id,
                resources=resources,
            )
            raise ResourceIndicatorError("resource_not_allowed")
        if granted and not set(granted).issuperset(resources):
            LOGGER.info(
                "Requested resource is not part of the grant",
                client_id=client.client_id,
                resources=resources,
                granted=granted,
            )
            raise ResourceIndicatorError("resource_not_granted")
        if len(join_resources(resources) or "") > GRANT_RESOURCE_MAX_LENGTH:
            raise ResourceIndicatorError("resource_too_long")
        return resources
