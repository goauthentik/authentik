"""API Authorization"""
from django.conf import settings
from django.db.models import Model
from django.db.models.query import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import get_authorization_header
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from authentik.api.authentication import validate_auth
from authentik.rbac.filters import ObjectFilter


class OwnerFilter(BaseFilterBackend):
    """Filter objects by their owner"""

    owner_key = "user"

    def filter_queryset(self, request: Request, queryset: QuerySet, view) -> QuerySet:
        if request.user.is_superuser:
            return queryset
        return queryset.filter(**{self.owner_key: request.user})


class SecretKeyFilter(DjangoFilterBackend):
    """Allow access to all objects when authenticated with secret key as token.

    Replaces both DjangoFilterBackend and ObjectFilter"""

    def filter_queryset(self, request: Request, queryset: QuerySet, view) -> QuerySet:
        auth_header = get_authorization_header(request)
        token = validate_auth(auth_header)
        if token and token == settings.SECRET_KEY:
            return queryset
        queryset = ObjectFilter().filter_queryset(request, queryset, view)
        return super().filter_queryset(request, queryset, view)


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
