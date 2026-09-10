from typing import TYPE_CHECKING

from requests import Request

if TYPE_CHECKING:
    from authentik.providers.scim.models import SCIMProvider


class SCIMTokenAuth:

    def __init__(self, provider: SCIMProvider):
        self.provider = provider

    def __call__(self, request: Request) -> Request:
        token = self.provider.secret.value if self.provider.secret else ""
        request.headers["Authorization"] = f"Bearer {token}"
        return request
