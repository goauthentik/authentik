"""Custom SCIM schemas"""
from typing import Optional

from pydanticscim.group import Group as SCIMGroupSchema
from pydanticscim.user import User as SCIMUserSchema


class User(SCIMUserSchema):
    """Modified User schema with added externalId field"""

    externalId: Optional[str] = None


class Group(SCIMGroupSchema):
    """Modified Group schema with added externalId field"""

    externalId: Optional[str] = None
