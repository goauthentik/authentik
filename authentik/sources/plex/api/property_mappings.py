"""Plex source property mappings API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.sources.plex.models import PlexSourcePropertyMapping


class PlexSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """PlexSourcePropertyMapping Serializer"""

    class Meta(PropertyMappingSerializer.Meta):
        model = PlexSourcePropertyMapping


class PlexSourcePropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for PlexSourcePropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = PlexSourcePropertyMapping


class PlexSourcePropertyMappingViewSet(ModelViewSet):
    """PlexSourcePropertyMapping Viewset"""

    queryset = PlexSourcePropertyMapping.objects.all()
    serializer_class = PlexSourcePropertyMappingSerializer
    filterset_class = PlexSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
