"""SCIM source property mappings API"""

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.scim.models import SCIMSourcePropertyMapping


class SCIMSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """SCIMSourcePropertyMapping Serializer"""

    class Meta:
        model = SCIMSourcePropertyMapping
        fields = PropertyMappingSerializer.Meta.fields


class SCIMSourcePropertyMappingFilter(FilterSet):
    """Filter for SCIMSourcePropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = SCIMSourcePropertyMapping
        fields = "__all__"


class SCIMSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """SCIMSourcePropertyMapping Viewset"""

    queryset = SCIMSourcePropertyMapping.objects.all()
    serializer_class = SCIMSourcePropertyMappingSerializer
    filterset_class = SCIMSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
