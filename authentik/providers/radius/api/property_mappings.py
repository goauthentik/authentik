"""Radius Property mappings API Views"""

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.radius.models import RadiusProviderPropertyMapping


class RadiusProviderPropertyMappingSerializer(PropertyMappingSerializer):
    """RadiusProviderPropertyMapping Serializer"""

    class Meta:
        model = RadiusProviderPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields


class RadiusProviderPropertyMappingFilter(FilterSet):
    """Filter for RadiusProviderPropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = RadiusProviderPropertyMapping
        fields = "__all__"


class RadiusProviderPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """RadiusProviderPropertyMapping Viewset"""

    queryset = RadiusProviderPropertyMapping.objects.all()
    serializer_class = RadiusProviderPropertyMappingSerializer
    filterset_class = RadiusProviderPropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
