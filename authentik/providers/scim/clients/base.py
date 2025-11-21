"""SCIM Client"""

from typing import TYPE_CHECKING

from django.core.cache import cache
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from pydantic import ValidationError
from requests import RequestException, Session

from authentik.lib.sync.outgoing import (
    HTTP_CONFLICT,
    HTTP_NO_CONTENT,
    HTTP_SERVICE_UNAVAILABLE,
    HTTP_TOO_MANY_REQUESTS,
)
from authentik.lib.sync.outgoing.base import SAFE_METHODS, BaseOutgoingSyncClient
from authentik.lib.sync.outgoing.exceptions import (
    DryRunRejected,
    NotFoundSyncException,
    ObjectExistsSyncException,
    TransientSyncException,
)
from authentik.lib.utils.http import get_http_session
from authentik.providers.scim.clients.exceptions import SCIMRequestException
from authentik.providers.scim.clients.schema import ServiceProviderConfiguration
from authentik.providers.scim.models import SCIMCompatibilityMode, SCIMProvider

if TYPE_CHECKING:
    from django.db.models import Model
    from pydantic import BaseModel

SERVICE_PROVIDER_CONFIG_CACHE_TIMEOUT = 3600


class SCIMClient[TModel: "Model", TConnection: "Model", TSchema: "BaseModel"](
    BaseOutgoingSyncClient[TModel, TConnection, TSchema, SCIMProvider]
):
    """SCIM Client"""

    base_url: str

    _session: Session
    _config: ServiceProviderConfiguration

    def __init__(self, provider: SCIMProvider):
        super().__init__(provider)
        self._session = get_http_session()
        self._session.verify = provider.verify_certificates
        self.provider = provider
        self.auth = provider.scim_auth()
        # Remove trailing slashes as we assume the URL doesn't have any
        base_url = provider.url
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self._config = self.get_service_provider_config()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Wrapper to send a request to the full URL"""
        if self.provider.dry_run and method.upper() not in SAFE_METHODS:
            raise DryRunRejected(f"{self.base_url}{path}", method, body=kwargs.get("json"))
        try:
            response = self._session.request(
                method,
                f"{self.base_url}{path}",
                **kwargs,
                auth=self.auth,
                headers={
                    "Accept": "application/scim+json",
                    "Content-Type": "application/scim+json",
                },
            )
        except RequestException as exc:
            raise SCIMRequestException(message="Failed to send request") from exc
        self.logger.debug("scim request", path=path, method=method, **kwargs)
        if response.status_code >= HttpResponseBadRequest.status_code:
            if response.status_code == HttpResponseNotFound.status_code:
                raise NotFoundSyncException(response)
            if response.status_code in [HTTP_TOO_MANY_REQUESTS, HTTP_SERVICE_UNAVAILABLE]:
                raise TransientSyncException()
            if response.status_code == HTTP_CONFLICT:
                raise ObjectExistsSyncException(response)
            self.logger.warning(
                "Failed to send SCIM request", path=path, method=method, response=response.text
            )
            raise SCIMRequestException(response)
        if response.status_code == HTTP_NO_CONTENT:
            return {}
        return response.json()

    def get_service_provider_config(self):
        """Get Service provider config"""
        default_config = ServiceProviderConfiguration.default()
        cache_key = f"goauthentik.io/providers/scim/{self.provider.pk}/service_provider_config"

        # Check cache first
        cached_config = cache.get(cache_key)
        if cached_config is not None:
            return cached_config

        # Attempt to fetch from remote
        path = "/ServiceProviderConfig"
        if self.provider.compatibility_mode == SCIMCompatibilityMode.SALESFORCE:
            path = "/ServiceProviderConfigs"

        try:
            config = ServiceProviderConfiguration.model_validate(self._request("GET", path))
            if self.provider.compatibility_mode == SCIMCompatibilityMode.AWS:
                config.patch.supported = False
            if self.provider.compatibility_mode == SCIMCompatibilityMode.SLACK:
                config.filter.supported = True
        except (ValidationError, SCIMRequestException, NotFoundSyncException) as exc:
            self.logger.warning(
                "failed to get ServiceProviderConfig, using default",
                exc=exc,
                provider=self.provider.name,
            )
            config = default_config

        # Cache the config (either successfully fetched or default)
        cache.set(cache_key, config, SERVICE_PROVIDER_CONFIG_CACHE_TIMEOUT)
        return config
