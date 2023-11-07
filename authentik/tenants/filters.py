"""Tenant API Filter"""
from django.db.models import QuerySet
from django.db.models.base import FieldDoesNotExist
from rest_framework.filters import BaseFilterBackend
from rest_framework.request import Request


class TenantFilter(BaseFilterBackend):
    """Filter that only returns objects for the current tenant"""

    def filter_queryset(self, request: Request, queryset: QuerySet, view) -> QuerySet:
        try:
            queryset.model._meta.get_field("tenant")
            return queryset.filter(tenant=request._request.tenant)
        except FieldDoesNotExist:
            return queryset
