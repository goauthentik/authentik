"""SAML source property mappings API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.saml.models import SAMLSourcePropertyMapping


class SAMLSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """SAMLSourcePropertyMapping Serializer"""

    class Meta(PropertyMappingSerializer.Meta):
        model = SAMLSourcePropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + ["list_merge_mode"]


class SAMLSourcePropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for SAMLSourcePropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = SAMLSourcePropertyMapping


class SAMLSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """SAMLSourcePropertyMapping Viewset"""

    queryset = SAMLSourcePropertyMapping.objects.all()
    serializer_class = SAMLSourcePropertyMappingSerializer
    filterset_class = SAMLSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
