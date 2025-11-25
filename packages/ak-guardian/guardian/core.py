from django.contrib.auth.models import Permission
from django.db.models import Model, Q
from django.utils.encoding import force_str

from guardian.ctypes import get_content_type
from guardian.utils import get_identity


def remove_app_label(perm: str) -> str:
    if "." in perm:
        _, perm = perm.split(".", 1)
    return perm


class ObjectPermissionChecker:
    """Generic object permissions checker class being the heart of `ak-guardian`.

    Note:
       Once checked for a single object, permissions are stored, and we don't hit
       the database again if another check is called for this object. This is great
       for templates, views or other request-based checks (assuming we don't
       have hundreds of permissions on a single object as we fetch all
       permissions for checked object).

       if we call `has_perm` for perm1/object1, then we
       change permission state and call `has_perm` again for same
       perm1/object1 on the same instance of ObjectPermissionChecker we won't see a
       difference as permissions are already fetched and stored within the cache
       dictionary.
    """

    def __init__(self, identity: Model | None = None) -> None:
        """Constructor for ObjectPermissionChecker.

        Parameters:
            identity (User | AnonymousUser | Group | Role): The identity to check permissions for.
        """
        self.user, self.group, self.role = get_identity(identity)  # type: ignore[arg-type] # None is not allowed
        self._obj_perms_cache: dict = {}

    def has_perm(self, perm: str, obj: Model | None = None) -> bool:
        """Checks if user/group/role has the specified permission for the given object.

        Parameters:
            perm (str): permission as string, may or may not contain app_label
                prefix (if not prefixed, we grab app_label from `obj`)
            obj (Model | None): Django's `Model` instance or `None` if querying a global permission.
                *Default* is `None`.

        Returns:
            True if user/group/role has the permission, False otherwise
        """
        if self.user and not self.user.is_active:
            return False
        elif self.user and self.user.is_superuser:
            return True

        perms = self.get_perms(obj)
        if "." not in perm:
            perms = {remove_app_label(perm) for perm in perms}

        return perm in perms

    def role_filter(self, related_name: str) -> dict:
        if self.user:
            return {f"{related_name}__role__in": self.user.all_roles()}
        elif self.group:
            return {f"{related_name}__role__in": self.group.all_roles()}
        elif self.role:
            return {f"{related_name}__role": self.role}
        return {}

    def object_filter(self, obj: Model) -> dict:
        from guardian.models import RoleObjectPermission

        related_name = RoleObjectPermission.permission.field.related_query_name()
        filter = {
            f"{related_name}__content_type": get_content_type(obj),
            f"{related_name}__object_pk": obj.pk,
        }
        filter.update(self.role_filter(related_name))

        return filter

    def model_filter(self) -> dict:
        from guardian.models import RoleModelPermission

        related_name = RoleModelPermission.permission.field.related_query_name()
        filter = self.role_filter(related_name)

        return filter

    def get_perms(self, obj: Model | None = None) -> set[str]:
        """Get a list of permissions for the given object.

        Parameters:
            obj (Model | None): Django's `Model` instance or `None` if querying a global permission.
                *Default* is `None`.

        Returns:
            set of codenames for all permissions for given `obj`.
        """
        if self.user and not self.user.is_active:
            return set()

        key = self.get_local_cache_key(obj)
        if key not in self._obj_perms_cache:
            if self.user and self.user.is_superuser:
                perms = Permission.objects.all()
                if obj:
                    perms = perms.filter(get_content_type(type(obj)))
            else:
                filter = Q(**self.model_filter())
                if obj:
                    filter |= Q(**self.object_filter(obj))
                perms = Permission.objects.filter(filter)

            perms_list = list(set(perms.values_list("content_type__app_label", "codename")))
            self._obj_perms_cache[key] = {f"{ct}.{name}" for ct, name in perms_list}
        return self._obj_perms_cache[key]

    def get_local_cache_key(self, obj: Model | None) -> tuple:
        """Returns cache key for `_obj_perms_cache` dict."""
        if not obj:
            return ("", "")
        ctype = get_content_type(obj)
        return ctype.id, force_str(obj.pk)
