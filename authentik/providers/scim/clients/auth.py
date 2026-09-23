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
        token = self.provider.token_ref.value if self.provider.token_ref else ""
        request.headers["Authorization"] = f"Bearer {token}"
        return request


class SCIMBasicAuth:
    """Authenticate SCIM requests with HTTP Basic credentials."""

    def __init__(self, provider: SCIMProvider):
        self.provider = provider

    def __call__(self, request: Request) -> Request:
        # requests' HTTPBasicAuth encodes credentials as latin-1, RFC 7617 expects UTF-8
        password = self.provider.auth_basic_password_ref
        credentials = f"{self.provider.auth_basic_user}:{password.value if password else ''}"
        encoded = b64encode(credentials.encode("utf-8")).decode()
        request.headers["Authorization"] = f"Basic {encoded}"
        return request
