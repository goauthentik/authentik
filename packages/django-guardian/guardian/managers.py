from typing import Any

from django.contrib.auth.models import Permission
from django.db import models
from django.db.models import Model, Q, QuerySet

from guardian.ctypes import get_content_type
from guardian.exceptions import ObjectNotPersisted


class BaseObjectPermissionManager(models.Manager):
    def assign_perm(self, perm: str, role: Any, obj: Model) -> Any:
        """Assigns permission with given `perm` for an instance `obj` and `role`."""
        if getattr(obj, "pk", None) is None:
            raise ObjectNotPersisted(f"Object {obj} needs to be persisted first")
        ctype = get_content_type(obj)
        if not isinstance(perm, Permission):
            permission = Permission.objects.get(content_type=ctype, codename=perm)
        else:
            permission = perm

        kwargs = {
            "permission": permission,
            "content_type": ctype,
            "object_pk": obj.pk,
            "role": role,
        }

        obj_perm, _ = self.get_or_create(**kwargs)
        return obj_perm

    def assign_perm_to_many(
        self, perm: str, roles: Any, obj: Model, ignore_conflicts: bool = False
    ) -> Any:
        """
        Bulk assigns given `perm` for the object `obj` to a set of roles.
        """
        ctype = get_content_type(obj)
        if not isinstance(perm, Permission):
            permission = Permission.objects.get(content_type=ctype, codename=perm)
        else:
            permission = perm

        kwargs = {
            "permission": permission,
            "content_type": ctype,
            "object_pk": obj.pk,
        }

        to_add = []
        for role in roles:
            kwargs["role"] = role
            to_add.append(self.model(**kwargs))

        return self.model.objects.bulk_create(to_add, ignore_conflicts=ignore_conflicts)

    def remove_perm(self, perm: str, role: Any, obj: Model) -> tuple[int, dict]:
        """
        Removes permission `perm` for an instance `obj` and given `role`.

        Please note that we do NOT fetch object permission from database -
        we use `Queryset.delete` method for removing it.
        The main implication of this is that `post_delete` signals would NOT be fired.
        """
        if getattr(obj, "pk", None) is None:
            raise ObjectNotPersisted(f"Object {obj} needs to be persisted first")

        filters = Q(**{"role": role})

        if isinstance(perm, Permission):
            filters &= Q(permission=perm)
        else:
            filters &= Q(permission__codename=perm, permission__content_type=get_content_type(obj))

        filters &= Q(object_pk=obj.pk)
        return self.filter(filters).delete()

    def bulk_remove_perm(self, perm: str, role: Any, queryset: QuerySet) -> tuple[int, dict]:
        """
        Removes permission `perm` for a `queryset` and given `role`.

        Please note that we do NOT fetch object permission from database -
        we use `Queryset.delete` method for removing it.
        The main implication of this is that `post_delete` signals would NOT be fired.
        """
        filters = Q(**{"role": role})

        if isinstance(perm, Permission):
            filters &= Q(permission=perm)
        else:
            ctype = get_content_type(queryset.model)
            filters &= Q(permission__codename=perm, permission__content_type=ctype)

        filters &= Q(object_pk__in=[str(pk) for pk in queryset.values_list("pk", flat=True)])

        return self.filter(filters).delete()


class UserObjectPermissionManager(BaseObjectPermissionManager):
    pass


class GroupObjectPermissionManager(BaseObjectPermissionManager):
    pass


class RoleObjectPermissionManager(BaseObjectPermissionManager):
    pass
