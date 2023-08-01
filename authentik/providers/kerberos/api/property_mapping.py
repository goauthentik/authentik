"""Kerberos Property mappings API Views"""
from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.kerberos.models import KerberosPrincipalMapping


class KerberosPrincipalMappingSerializer(PropertyMappingSerializer):
    """KerberosPrincipalMapping Serializer"""

    class Meta:
        model = KerberosPrincipalMapping
        fields = PropertyMappingSerializer.Meta.fields


class KerberosPrincipalMappingMappingFilter(FilterSet):
    """Filter for KerberosPrincipalMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = KerberosPrincipalMapping
        fields = "__all__"


class KerberosPrincipalMappingViewSet(UsedByMixin, ModelViewSet):
    """SCIMMapping Viewset"""

    queryset = KerberosPrincipalMapping.objects.all()
    serializer_class = KerberosPrincipalMappingSerializer
    filterset_class = KerberosPrincipalMappingMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
