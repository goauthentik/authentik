"""API Authorization"""
from django.db.models import Model
from django.db.models.query import QuerySet
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class OwnerFilter(BaseFilterBackend):
    """Filter objects by their owner"""

    owner_key = "user"

    def filter_queryset(self, request: Request, queryset: QuerySet, view) -> QuerySet:
        if request.user.is_superuser:
            return queryset
        return queryset.filter(**{self.owner_key: request.user})


class OwnerPermissions(BasePermission):
    """Authorize requests by an object's owner matching the requesting user"""

    owner_key = "user"

    def has_permission(self, request: Request, view) -> bool:
        """If the user is authenticated, we allow all requests here. For listing, the
        object-level permissions are done by the filter backend"""
        return request.user.is_authenticated

    def has_object_permission(self, request: Request, view, obj: Model) -> bool:
        """Check if the object's owner matches the currently logged in user"""
        if not hasattr(obj, self.owner_key):
            return False
        owner = getattr(obj, self.owner_key)
        if owner != request.user:
            return False
        return True


class OwnerSuperuserPermissions(OwnerPermissions):
    """Similar to OwnerPermissions, except always allow access for superusers"""

    def has_object_permission(self, request: Request, view, obj: Model) -> bool:
        if request.user.is_superuser:
            return True
        return super().has_object_permission(request, view, obj)
