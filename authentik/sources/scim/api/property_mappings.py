"""SCIM source property mappings API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.scim.models import SCIMSourcePropertyMapping


class SCIMSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """SCIMSourcePropertyMapping Serializer"""

    class Meta:
        model = SCIMSourcePropertyMapping
        fields = PropertyMappingSerializer.Meta.fields


class SCIMSourcePropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for SCIMSourcePropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = SCIMSourcePropertyMapping


class SCIMSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """SCIMSourcePropertyMapping Viewset"""

    queryset = SCIMSourcePropertyMapping.objects.all()
    serializer_class = SCIMSourcePropertyMappingSerializer
    filterset_class = SCIMSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
