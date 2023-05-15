"""Custom SCIM schemas"""
from typing import Optional

from pydanticscim.group import Group as BaseGroup
from pydanticscim.responses import PatchRequest as BasePatchRequest
from pydanticscim.responses import SCIMError as BaseSCIMError
from pydanticscim.service_provider import Bulk, ChangePassword, Filter, Patch
from pydanticscim.service_provider import (
    ServiceProviderConfiguration as BaseServiceProviderConfiguration,
)
from pydanticscim.service_provider import Sort
from pydanticscim.user import User as BaseUser


class User(BaseUser):
    """Modified User schema with added externalId field"""

    externalId: Optional[str] = None


class Group(BaseGroup):
    """Modified Group schema with added externalId field"""

    externalId: Optional[str] = None


class ServiceProviderConfiguration(BaseServiceProviderConfiguration):
    """ServiceProviderConfig with fallback"""

    _is_fallback: Optional[bool] = False

    @property
    def is_fallback(self) -> bool:
        """Check if this service provider config was retrieved from the API endpoint
        or a fallback was used"""
        return self._is_fallback

    @staticmethod
    def default() -> "ServiceProviderConfiguration":
        """Get default configuration, which doesn't support any optional features as fallback"""
        return ServiceProviderConfiguration(
            patch=Patch(supported=False),
            bulk=Bulk(supported=False),
            filter=Filter(supported=False),
            changePassword=ChangePassword(supported=False),
            sort=Sort(supported=False),
            authenticationSchemes=[],
            _is_fallback=True,
        )


class PatchRequest(BasePatchRequest):
    """PatchRequest which correctly sets schemas"""

    schemas: tuple[str] = ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]


class SCIMError(BaseSCIMError):
    """SCIM error with optional status code"""

    status: Optional[int]
