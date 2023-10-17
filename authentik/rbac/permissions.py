"""RBAC Permissions"""
from django.db.models import Model
from rest_framework.permissions import BasePermission, DjangoObjectPermissions
from rest_framework.request import Request


class ObjectPermissions(DjangoObjectPermissions):
    """RBAC Permissions"""

    def has_object_permission(self, request: Request, view, obj: Model):
        queryset = self._queryset(view)
        model_cls = queryset.model
        perms = self.get_required_object_permissions(request.method, model_cls)
        # Rank global permissions higher than per-object permissions
        if request.user.has_perms(perms):
            return True
        return super().has_object_permission(request, view, obj)


# pylint: disable=invalid-name
def HasPermission(*perm: str) -> type[BasePermission]:
    """Permission checker for any non-object permissions, returns
    a BasePermission class that can be used with rest_framework"""

    # pylint: disable=missing-class-docstring, invalid-name
    class checker(BasePermission):
        def has_permission(self, request: Request, view):
            return bool(request.user and request.user.has_perms(perm))

    return checker
