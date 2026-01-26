from typing import TYPE_CHECKING

from requests import Request

if TYPE_CHECKING:
    from authentik.providers.scim.models import SCIMProvider


class SCIMTokenAuth:

    def __init__(self, provider: SCIMProvider):
        self.provider = provider

    def __call__(self, request: Request) -> Request:
        request.headers["Authorization"] = f"Bearer {self.provider.token}"
        return request
