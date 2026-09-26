"""On-demand discovery of the resource types advertised by a SCIM destination."""

from dataclasses import dataclass, replace
from datetime import datetime
from http import HTTPStatus
from typing import Literal

from django.core.cache import cache
from django.utils.timezone import now
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from authentik.lib.sync.outgoing.exceptions import BaseSyncException
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.models import SCIMProvider

MAX_DISCOVERY_PAGES = 100
LIST_RESPONSE_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:ListResponse"


class DiscoverySchema(BaseModel):
    """SCIM attribute names are case insensitive."""

    model_config = ConfigDict(alias_generator=str.lower, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, value):
        if isinstance(value, dict):
            return {key.lower(): item for key, item in value.items()}
        return value


class ResourceTypeExtension(DiscoverySchema):
    schema_uri: str = Field(alias="schema", min_length=1)
    required: bool


class ResourceType(DiscoverySchema):
    id: str | None = None
    name: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    description: str | None = None
    schema_uri: str = Field(alias="schema", min_length=1)
    schema_extensions: list[ResourceTypeExtension] = Field(
        default_factory=list, alias="schemaextensions"
    )


class ResourceTypePage(DiscoverySchema):
    schemas: list[str]
    total_results: int = Field(alias="totalresults", ge=0)
    start_index: int | None = Field(default=None, alias="startindex", ge=1)
    items_per_page: int | None = Field(default=None, alias="itemsperpage", ge=0)
    resources: list[ResourceType] = Field(default_factory=list)


@dataclass
class ResourceTypeDiscovery:
    status: Literal["success", "unavailable", "error"]
    resource_types: list[ResourceType]
    fetched_at: datetime
    cached: bool = False
    detail: str = ""


class SCIMResourceTypesClient(SCIMClient):
    """Read destination metadata without fetching unrelated configuration or syncing objects."""

    def __init__(self, provider: SCIMProvider):
        super().__init__(provider, initialize=False)

    def get_resource_types(self, *, force_refresh: bool = False) -> ResourceTypeDiscovery:
        """Return a complete listing, or an explicit unavailable/error diagnostic.

        ResourceTypes uses the ServiceProviderConfig cache duration, with a separate cache key.
        Failed requests are not cached; a failed refresh also discards the previous result.
        """
        key = f"goauthentik.io/providers/scim/{self.provider.pk}/resource_types"
        timeout = self.provider.service_provider_config_cache_timeout_seconds
        if not force_refresh and timeout > 0:
            if cached := cache.get(key):
                return replace(cached, cached=True)
        cache.delete(key)
        try:
            self.auth = self.provider.scim_auth()
        except BaseSyncException:
            # A token endpoint failure is not evidence that ResourceTypes is unavailable.
            return ResourceTypeDiscovery(
                "error",
                [],
                now(),
                detail="Unable to initialize SCIM authentication. Check the provider's credentials "
                "and OAuth configuration.",
            )
        try:
            resources = self._fetch_resource_types()
            result = ResourceTypeDiscovery("success", resources, now())
        except ValidationError, ValueError:
            result = ResourceTypeDiscovery(
                "error",
                [],
                now(),
                detail="The destination returned an invalid ResourceTypes listing.",
            )
        except BaseSyncException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in (HTTPStatus.NOT_FOUND, HTTPStatus.NOT_IMPLEMENTED):
                result = ResourceTypeDiscovery(
                    "unavailable",
                    [],
                    now(),
                    detail=f"ResourceTypes is unavailable (HTTP {status_code}).",
                )
            else:
                detail = (
                    f"ResourceTypes request failed (HTTP {status_code})."
                    if status_code is not None
                    else "Unable to retrieve ResourceTypes from the destination."
                )
                result = ResourceTypeDiscovery("error", [], now(), detail=detail)
        if timeout > 0 and result.status != "error":
            cache.set(key, result, timeout)
        return result

    def _fetch_resource_types(self) -> list[ResourceType]:
        resources = []
        total_results = None
        start_index = 1
        for _ in range(MAX_DISCOVERY_PAGES):
            page = ResourceTypePage.model_validate(
                self._request(
                    "GET", "/ResourceTypes", params={"startIndex": start_index, "count": 100}
                )
            )
            if LIST_RESPONSE_SCHEMA not in page.schemas:
                raise ValueError("Missing ListResponse schema")
            if total_results is None:
                total_results = page.total_results
            if page.total_results != total_results:
                raise ValueError("ResourceTypes changed during pagination")
            if page.start_index is not None and page.start_index != start_index:
                raise ValueError("ResourceTypes pagination did not advance")
            if page.items_per_page is not None and page.items_per_page != len(page.resources):
                raise ValueError("ResourceTypes page size does not match its resources")
            resources.extend(page.resources)
            if len(resources) > total_results:
                raise ValueError("ResourceTypes exceeds totalResults")
            if len({resource.name.casefold() for resource in resources}) != len(resources):
                raise ValueError("Duplicate resource types")
            if len(resources) == total_results:
                return resources
            if not page.resources:
                raise ValueError("Incomplete ResourceTypes listing")
            start_index += len(page.resources)
        raise ValueError("ResourceTypes pagination limit exceeded")
