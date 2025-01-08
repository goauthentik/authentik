"""API Authorization"""

from django.conf import settings
from django.db.models.query import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import get_authorization_header
from rest_framework.request import Request

from authentik.api.authentication import validate_auth
from authentik.rbac.filters import ObjectFilter


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
