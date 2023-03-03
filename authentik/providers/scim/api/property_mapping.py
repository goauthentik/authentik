"""scim Property mappings API Views"""
from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.scim.models import SCIMMapping


class SCIMMappingSerializer(PropertyMappingSerializer):
    """SCIMMapping Serializer"""

    class Meta:
        model = SCIMMapping
        fields = PropertyMappingSerializer.Meta.fields


class SCIMMappingFilter(FilterSet):
    """Filter for SCIMMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = SCIMMapping
        fields = "__all__"


class SCIMMappingViewSet(UsedByMixin, ModelViewSet):
    """SCIMMapping Viewset"""

    queryset = SCIMMapping.objects.all()
    serializer_class = SCIMMappingSerializer
    filterset_class = SCIMMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
