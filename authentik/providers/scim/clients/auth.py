from base64 import b64encode
from typing import TYPE_CHECKING

from requests import Request

if TYPE_CHECKING:
    from authentik.providers.scim.models import SCIMProvider


class SCIMTokenAuth:
    """Authenticate SCIM requests with a static bearer token."""

    def __init__(self, provider: SCIMProvider):
        self.provider = provider

    def __call__(self, request: Request) -> Request:
        request.headers["Authorization"] = f"Bearer {self.provider.token}"
        return request


class SCIMBasicAuth:
    """Authenticate SCIM requests with HTTP Basic credentials."""

    def __init__(self, provider: SCIMProvider):
        self.provider = provider

    def __call__(self, request: Request) -> Request:
        # requests' HTTPBasicAuth encodes credentials as latin-1, RFC 7617 expects UTF-8
        credentials = f"{self.provider.auth_basic_user}:{self.provider.auth_basic_password}"
        encoded = b64encode(credentials.encode("utf-8")).decode()
        request.headers["Authorization"] = f"Basic {encoded}"
        return request
