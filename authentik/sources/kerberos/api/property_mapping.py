"""Kerberos Property Mapping API"""
from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.kerberos.models import KerberosPropertyMapping


class KerberosPropertyMappingSerializer(PropertyMappingSerializer):
    """Kerberos PropertyMapping Serializer"""

    class Meta:
        model = KerberosPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields


class KerberosPropertyMappingFilter(FilterSet):
    """Filter for KerberosPropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = KerberosPropertyMapping
        fields = "__all__"


class KerberosPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """Kerberos PropertyMapping Viewset"""

    queryset = KerberosPropertyMapping.objects.all()
    serializer_class = KerberosPropertyMappingSerializer
    filterset_class = KerberosPropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
