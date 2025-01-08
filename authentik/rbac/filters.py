"""RBAC API Filter"""

from django.conf import settings
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_guardian.filters import ObjectPermissionsFilter

from authentik.api.authentication import validate_auth
from authentik.core.models import UserTypes


class ObjectFilter(ObjectPermissionsFilter):
    """Object permission filter that grants global permission higher priority than
    per-object permissions"""

    def filter_queryset(self, request: Request, queryset: QuerySet, view: APIView) -> QuerySet:
        permission = self.perm_format % {
            "app_label": queryset.model._meta.app_label,
            "model_name": queryset.model._meta.model_name,
        }
        # having the global permission set on a user has higher priority than
        # per-object permissions
        if request.user.has_perm(permission):
            return queryset
        queryset = super().filter_queryset(request, queryset, view)
        # Outposts (which are the only objects using internal service accounts)
        # except requests to return an empty list when they have no objects
        # assigned
        if getattr(request.user, "type", None) == UserTypes.INTERNAL_SERVICE_ACCOUNT:
            return queryset
        # User does not have permissions, but we have an owner field defined, so filter by that
        if owner_field := getattr(view, "owner_field", None):
            return queryset.filter(**{owner_field: request.user})
        if not queryset.exists():
            # User doesn't have direct permission to all objects
            # and also no object permissions assigned (directly or via role)
            raise PermissionDenied()
        return queryset


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
