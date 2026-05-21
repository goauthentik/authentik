"""Helpers for SCIM source managed-objects-only mode."""

from django.db.models import QuerySet

from authentik.core.models import Group, User
from authentik.sources.scim.models import SCIMSource, SCIMSourceGroup, SCIMSourceUser
from authentik.sources.scim.views.v2.exceptions import (
    SCIMConflictError,
    SCIMError,
    SCIMErrorTypes,
    SCIMValidationError,
)


def resolve_user(
    source: SCIMSource, connection: SCIMSourceUser | None, username: str
) -> User:
    """Resolve the user to create or update for a SCIM request."""
    if connection:
        return connection.user
    if source.managed_objects_only:
        if User.objects.filter(username=username).exists():
            raise SCIMConflictError("User with this userName already exists.")
        return User()
    if existing := User.objects.filter(username=username).first():
        return existing
    return User()


def resolve_group(source: SCIMSource, connection: SCIMSourceGroup | None, name: str) -> Group:
    """Resolve the group to create or update for a SCIM request."""
    if connection:
        return connection.group
    if source.managed_objects_only:
        if Group.objects.filter(name=name).exists():
            raise SCIMConflictError("Group with this displayName already exists.")
        return Group()
    if existing := Group.objects.filter(name=name).first():
        return existing
    return Group()


def filter_group_members(source: SCIMSource, users: QuerySet[User]) -> QuerySet[User]:
    """Filter group members to users managed by this source when required."""
    if not source.managed_objects_only:
        return users
    managed = users.filter(scimsourceuser__source=source).distinct()
    if users.count() != managed.count():
        raise SCIMValidationError(
            SCIMError(
                detail="One or more group members are not managed by this SCIM source.",
                scimType=SCIMErrorTypes.invalid_value,
                status=400,
            )
        )
    return managed
