"""API Authorization"""
from django.db.models import Model
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


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
