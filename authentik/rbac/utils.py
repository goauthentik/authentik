"""RBAC utils"""
from typing import Optional

from django.db.models import Model, Q
from django.db.transaction import atomic
from guardian.models import GroupObjectPermission, UserObjectPermission

from authentik.core.models import User
from authentik.rbac.models import Role


@atomic
def unassign_perm(permissions: list[str], user_or_role: User | Role, obj: Optional[Model]):
    """Unassign global or object permission from user or role."""
    to_remove = Q()
    permission_qs = None
    if obj:
        for perm in permissions:
            app_label, _, codename = perm.partition(".")
            to_remove &= Q(
                permission__content_type__app_label=app_label,
                permission__codename=codename,
            )
        if isinstance(user_or_role, User):
            permission_qs = UserObjectPermission.objects.filter(user=user_or_role)
        else:
            permission_qs = GroupObjectPermission.objects.filter(group=user_or_role.group)
    else:
        for perm in permissions:
            app_label, _, codename = perm.partition(".")
            to_remove &= Q(
                content_type__app_label=app_label,
                codename=codename,
            )

    if obj:
        permission_qs.filter(object_pk=obj.pk).filter(to_remove).delete()
        return
    elif isinstance(user_or_role, User):
        user_or_role.user_permissions.set(user_or_role.user_permissions.all().exclude(to_remove))
    else:
        user_or_role.group.permissions.set(user_or_role.group.permissions.all().exclude(to_remove))
