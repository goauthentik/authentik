"""SCIM Client"""
from typing import Generic, TypeVar

from pydantic import ValidationError
from pydanticscim.service_provider import (
    Bulk,
    ChangePassword,
    Filter,
    Patch,
    ServiceProviderConfiguration,
    Sort,
)
from requests import RequestException, Session
from structlog.stdlib import get_logger

from authentik.lib.utils.http import get_http_session
from authentik.providers.scim.clients.exceptions import SCIMRequestException
from authentik.providers.scim.models import SCIMProvider

T = TypeVar("T")
# pylint: disable=invalid-name
SchemaType = TypeVar("SchemaType")


class SCIMClient(Generic[T, SchemaType]):
    """SCIM Client"""

    base_url: str
    token: str
    provider: SCIMProvider

    _session: Session
    _config: ServiceProviderConfiguration

    def __init__(self, provider: SCIMProvider):
        self._session = get_http_session()
        self.provider = provider
        # Remove trailing slashes as we assume the URL doesn't have any
        base_url = provider.url
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.token = provider.token
        self.logger = get_logger().bind(provider=provider.name)
        self._config = self.get_service_provider_config()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Wrapper to send a request to the full URL"""
        try:
            response = self._session.request(
                method,
                f"{self.base_url}{path}",
                **kwargs,
                headers={"Authorization": f"Bearer {self.token}"},
            )
        except RequestException as exc:
            raise SCIMRequestException(None) from exc
        self.logger.debug("scim request", path=path, method=method, **kwargs)
        if response.status_code >= 400:
            self.logger.warning(
                "Failed to send SCIM request", path=path, method=method, response=response.text
            )
            raise SCIMRequestException(response)
        if response.status_code == 204:
            return {}
        return response.json()

    def get_service_provider_config(self):
        """Get Service provider config"""
        default_config = ServiceProviderConfiguration(
            patch=Patch(supported=False),
            bulk=Bulk(supported=False),
            filter=Filter(supported=False),
            changePassword=ChangePassword(supported=False),
            sort=Sort(supported=False),
            authenticationSchemes=[],
        )
        try:
            return ServiceProviderConfiguration.parse_obj(
                self._request("GET", "/ServiceProviderConfig")
            )
        except ValidationError as exc:
            self.logger.warning("ServiceProviderConfig invalid", exc=exc)
            return default_config

    def write(self, obj: T):
        """Write object to SCIM"""
        raise NotImplementedError()

    def delete(self, obj: T):
        """Delete object from SCIM"""
        raise NotImplementedError()

    def to_scim(self, obj: T) -> SchemaType:
        """Convert object to scim"""
        raise NotImplementedError()
