"""SAML Property mappings API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.saml.models import SAMLPropertyMapping


class SAMLPropertyMappingSerializer(PropertyMappingSerializer):
    """SAMLPropertyMapping Serializer"""

    class Meta:
        model = SAMLPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + [
            "saml_name",
            "friendly_name",
        ]


class SAMLPropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for SAMLPropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = SAMLPropertyMapping
        fields = PropertyMappingFilterSet.Meta.fields + ["saml_name", "friendly_name"]


class SAMLPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """SAMLPropertyMapping Viewset"""

    queryset = SAMLPropertyMapping.objects.all()
    serializer_class = SAMLPropertyMappingSerializer
    filterset_class = SAMLPropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
