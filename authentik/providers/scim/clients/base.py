"""SCIM Client"""

from typing import TYPE_CHECKING

from django.http import HttpResponseBadRequest, HttpResponseNotFound
from pydantic import ValidationError
from requests import RequestException, Session

from authentik.lib.sync.outgoing import (
    HTTP_CONFLICT,
    HTTP_NO_CONTENT,
    HTTP_SERVICE_UNAVAILABLE,
    HTTP_TOO_MANY_REQUESTS,
)
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectExistsSyncException,
    TransientSyncException,
)
from authentik.lib.utils.http import get_http_session
from authentik.providers.scim.clients.exceptions import SCIMRequestException
from authentik.providers.scim.clients.schema import ServiceProviderConfiguration
from authentik.providers.scim.models import SCIMProvider

if TYPE_CHECKING:
    from django.db.models import Model
    from pydantic import BaseModel


class SCIMClient[TModel: "Model", TConnection: "Model", TSchema: "BaseModel"](
    BaseOutgoingSyncClient[TModel, TConnection, TSchema, SCIMProvider]
):
    """SCIM Client"""

    base_url: str
    token: str

    _session: Session
    _config: ServiceProviderConfiguration

    def __init__(self, provider: SCIMProvider):
        super().__init__(provider)
        self._session = get_http_session()
        self.provider = provider
        # Remove trailing slashes as we assume the URL doesn't have any
        base_url = provider.url
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.token = provider.token
        self._config = self.get_service_provider_config()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Wrapper to send a request to the full URL"""
        try:
            response = self._session.request(
                method,
                f"{self.base_url}{path}",
                **kwargs,
                headers={
                    "Authorization": f"Bearer {self.token}",
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
        try:
            return ServiceProviderConfiguration.model_validate(
                self._request("GET", "/ServiceProviderConfig")
            )
        except (ValidationError, SCIMRequestException) as exc:
            self.logger.warning("failed to get ServiceProviderConfig", exc=exc)
            return default_config
