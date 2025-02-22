"""Radius Property mappings API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.radius.models import RadiusProviderPropertyMapping


class RadiusProviderPropertyMappingSerializer(PropertyMappingSerializer):
    """RadiusProviderPropertyMapping Serializer"""

    class Meta:
        model = RadiusProviderPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields


class RadiusProviderPropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for RadiusProviderPropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = RadiusProviderPropertyMapping


class RadiusProviderPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """RadiusProviderPropertyMapping Viewset"""

    queryset = RadiusProviderPropertyMapping.objects.all()
    serializer_class = RadiusProviderPropertyMappingSerializer
    filterset_class = RadiusProviderPropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
