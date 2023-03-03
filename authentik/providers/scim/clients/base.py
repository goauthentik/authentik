"""SCIM Client"""
from typing import Generic, TypeVar

from pydanticscim.service_provider import ServiceProviderConfiguration
from requests import Session
from structlog.stdlib import get_logger

from authentik.lib.utils.http import get_http_session
from authentik.providers.scim.clients.exceptions import SCIMRequestException
from authentik.providers.scim.models import SCIMProvider

T = TypeVar("T")


class SCIMClient(Generic[T]):
    """SCIM Client"""

    base_url: str
    token: str
    provider: SCIMProvider

    _session: Session
    # _config: ServiceProviderConfiguration

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
        # self._config = self.get_service_provider_config()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Wrapper to send a request to the full URL"""
        response = self._session.request(
            method,
            f"{self.base_url}{path}",
            **kwargs,
            headers={"Authorization": f"Bearer {self.token}"},
        )
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
        return ServiceProviderConfiguration(**self._request("GET", "/ServiceProviderConfig"))

    def write(self, obj: T):
        """Write object to SCIM"""
        raise NotImplementedError()

    def delete(self, obj: T):
        """Delete object from SCIM"""
        raise NotImplementedError()
