"""Custom SCIM schemas"""

from enum import Enum

from pydantic import AnyUrl, BaseModel, ConfigDict, Field
from pydanticscim.group import Group as BaseGroup
from pydanticscim.responses import PatchOperation as BasePatchOperation
from pydanticscim.responses import PatchRequest as BasePatchRequest
from pydanticscim.responses import SCIMError as BaseSCIMError
from pydanticscim.service_provider import Bulk as BaseBulk
from pydanticscim.service_provider import ChangePassword, Filter, Patch, Sort
from pydanticscim.service_provider import (
    ServiceProviderConfiguration as BaseServiceProviderConfiguration,
)
from pydanticscim.user import AddressKind
from pydanticscim.user import User as BaseUser

SCIM_USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_GROUP_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"


class Address(BaseModel):
    formatted: str | None = Field(
        None,
        description="The full mailing address, formatted for display "
        "or use with a mailing label.  This attribute MAY contain newlines.",
    )
    streetAddress: str | None = Field(
        None,
        description="The full street address component, which may "
        "include house number, street name, P.O. box, and multi-line "
        "extended street address information.  This attribute MAY contain newlines.",
    )
    locality: str | None = Field(None, description="The city or locality component.")
    region: str | None = Field(None, description="The state or region component.")
    postalCode: str | None = Field(None, description="The zip code or postal code component.")
    country: str | None = Field(None, description="The country name component.")
    type: AddressKind | None = Field(
        None,
        description="A label indicating the attribute's function, e.g., 'work' or 'home'.",
    )
    primary: bool | None = None


class Manager(BaseModel):
    value: str | None = Field(
        None,
        description="The id of the SCIM resource representingthe User's manager.  REQUIRED.",
    )
    ref: AnyUrl | None = Field(
        None,
        alias="$ref",
        description="The URI of the SCIM resource representing the User's manager.  REQUIRED.",
    )
    displayName: str | None = Field(
        None,
        description="The displayName of the User's manager. OPTIONAL and READ-ONLY.",
    )


class EnterpriseUser(BaseModel):
    employeeNumber: str | None = Field(
        None,
        description="Numeric or alphanumeric identifier assigned to a person, "
        "typically based on order of hire or association with anorganization.",
    )
    costCenter: str | None = Field(None, description="Identifies the name of a cost center.")
    organization: str | None = Field(None, description="Identifies the name of an organization.")
    division: str | None = Field(None, description="Identifies the name of a division.")
    department: str | None = Field(
        None,
        description="Numeric or alphanumeric identifier assigned to a person,"
        " typically based on order of hire or association with anorganization.",
    )
    manager: Manager | None = Field(
        None,
        description="The User's manager. A complex type that optionally allows "
        "service providers to represent organizational hierarchy by referencing"
        " the 'id' attribute of another User.",
    )


class User(BaseUser):
    """Modified User schema with added externalId field"""

    model_config = ConfigDict(serialize_by_alias=True, extra="allow")

    id: str | int | None = None
    schemas: list[str] = [SCIM_USER_SCHEMA]
    externalId: str | None = None
    meta: dict | None = None
    addresses: list[Address] | None = Field(
        None,
        description=(
            "A physical mailing address for this User. Canonical type "
            "values of 'work', 'home', and 'other'."
        ),
    )
    enterprise_user: EnterpriseUser | None = Field(
        default=None,
        alias="urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
        serialization_alias="urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
    )


class Group(BaseGroup):
    """Modified Group schema with added externalId field"""

    model_config = ConfigDict(extra="allow")

    id: str | int | None = None
    schemas: list[str] = [SCIM_GROUP_SCHEMA]
    externalId: str | None = None
    meta: dict | None = None


class Bulk(BaseBulk):

    maxOperations: int = Field()


class ServiceProviderConfiguration(BaseServiceProviderConfiguration):
    """ServiceProviderConfig with fallback"""

    _is_fallback: bool | None = False
    bulk: Bulk = Field(..., description="A complex type that specifies bulk configuration options.")

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
            bulk=Bulk(supported=False, maxOperations=0),
            filter=Filter(supported=False),
            changePassword=ChangePassword(supported=False),
            sort=Sort(supported=False),
            authenticationSchemes=[],
            _is_fallback=True,
        )


class PatchOp(str, Enum):

    replace = "replace"
    remove = "remove"
    add = "add"

    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        for member in cls:
            if member.lower() == value:
                return member
        return None


class PatchRequest(BasePatchRequest):
    """PatchRequest which correctly sets schemas"""

    schemas: tuple[str] = ("urn:ietf:params:scim:api:messages:2.0:PatchOp",)


class PatchOperation(BasePatchOperation):
    """PatchOperation with optional path"""

    op: PatchOp
    path: str | None = None


class SCIMError(BaseSCIMError):
    """SCIM error with optional status code"""

    status: int | None
