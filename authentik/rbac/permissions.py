"""RBAC Permissions"""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from guardian.shortcuts import assign_perm
from rest_framework.permissions import BasePermission, DjangoObjectPermissions
from rest_framework.request import Request

from authentik.rbac.models import InitialPermissions, InitialPermissionsMode


class ObjectPermissions(DjangoObjectPermissions):
    """RBAC Permissions"""

    def has_permission(self, request: Request, view) -> bool:
        """Always grant permission for object-specific requests
        as view permission checking is done by `ObjectFilter`,
        and write permission checking is done by `has_object_permission`"""
        lookup = getattr(view, "lookup_url_kwarg", None) or getattr(view, "lookup_field", None)
        if lookup and lookup in view.kwargs:
            return True
        # Legacy behaviour:
        # Allow creation of objects even without explicit permission
        queryset = self._queryset(view)
        required_perms = self.get_required_permissions(request.method, queryset.model)
        if (
            len(required_perms) == 1
            and f"{queryset.model._meta.app_label}.add_{queryset.model._meta.model_name}"
            in required_perms
            and getattr(view, "rbac_allow_create_without_perm", False)
        ):
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request: Request, view, obj: Model) -> bool:
        queryset = self._queryset(view)
        model_cls = queryset.model
        perms = self.get_required_object_permissions(request.method, model_cls)
        # Rank global permissions higher than per-object permissions
        if request.user.has_perms(perms):
            return True
        # Allow access for owners if configured
        if owner_field := getattr(view, "owner_field", None):
            if getattr(obj, owner_field) == request.user:
                return True
        return super().has_object_permission(request, view, obj)


def HasPermission(*perm: str) -> type[BasePermission]:
    """Permission checker for any non-object permissions, returns
    a BasePermission class that can be used with rest_framework"""

    class checker(BasePermission):
        def has_permission(self, request: Request, view):
            return bool(request.user and request.user.has_perms(perm))

    return checker


# TODO: add `user: User` type annotation without circular dependencies.
# The author of this function isn't proficient/patient enough to do it.
def assign_initial_permissions(user, instance: Model):
    # Performance here should not be an issue, but if needed, there are many optimization routes
    initial_permissions_list = InitialPermissions.objects.filter(role__group__in=user.groups.all())
    for initial_permissions in initial_permissions_list:
        for permission in initial_permissions.permissions.all():
            if permission.content_type != ContentType.objects.get_for_model(instance):
                continue
            assign_to = (
                user
                if initial_permissions.mode == InitialPermissionsMode.USER
                else initial_permissions.role.group
            )
            assign_perm(permission, assign_to, instance)
