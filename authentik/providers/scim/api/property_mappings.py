"""scim Property mappings API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.scim.models import SCIMMapping


class SCIMMappingSerializer(PropertyMappingSerializer):
    """SCIMMapping Serializer"""

    class Meta:
        model = SCIMMapping
        fields = PropertyMappingSerializer.Meta.fields


class SCIMMappingFilter(PropertyMappingFilterSet):
    """Filter for SCIMMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = SCIMMapping


class SCIMMappingViewSet(UsedByMixin, ModelViewSet):
    """SCIMMapping Viewset"""

    queryset = SCIMMapping.objects.all()
    serializer_class = SCIMMappingSerializer
    filterset_class = SCIMMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
