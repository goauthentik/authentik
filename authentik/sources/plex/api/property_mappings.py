"""Plex source property mappings API"""

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.plex.models import PlexSourcePropertyMapping


class PlexSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """PlexSourcePropertyMapping Serializer"""

    class Meta:
        model = PlexSourcePropertyMapping
        fields = PropertyMappingSerializer.Meta.fields


class PlexSourcePropertyMappingFilter(FilterSet):
    """Filter for PlexSourcePropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = PlexSourcePropertyMapping
        fields = "__all__"


class PlexSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """PlexSourcePropertyMapping Viewset"""

    queryset = PlexSourcePropertyMapping.objects.all()
    serializer_class = PlexSourcePropertyMappingSerializer
    filterset_class = PlexSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
