"""RBAC Permissions"""

from django.db.models import Model
from rest_framework.permissions import BasePermission, DjangoObjectPermissions
from rest_framework.request import Request


class ObjectPermissions(DjangoObjectPermissions):
    """RBAC Permissions"""

    def has_permission(self, request: Request, view) -> bool:
        """Always grant permission for object-specific requests
        as view permission checking is done by `ObjectFilter`,
        and write permission checking is done by `has_object_permission`"""
        lookup = getattr(view, "lookup_url_kwarg", None) or getattr(view, "lookup_field", None)
        if lookup and lookup in view.kwargs:
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request: Request, view, obj: Model) -> bool:
        queryset = self._queryset(view)
        model_cls = queryset.model
        perms = self.get_required_object_permissions(request.method, model_cls)
        # Rank global permissions higher than per-object permissions
        if request.user.has_perms(perms):
            return True
        return super().has_object_permission(request, view, obj)


def HasPermission(*perm: str) -> type[BasePermission]:
    """Permission checker for any non-object permissions, returns
    a BasePermission class that can be used with rest_framework"""

    class checker(BasePermission):
        def has_permission(self, request: Request, view):
            return bool(request.user and request.user.has_perms(perm))

    return checker
