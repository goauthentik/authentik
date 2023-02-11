"""SAML Property mappings API Views"""
from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
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


class SAMLPropertyMappingFilter(FilterSet):
    """Filter for SAMLPropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = SAMLPropertyMapping
        fields = "__all__"


class SAMLPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """SAMLPropertyMapping Viewset"""

    queryset = SAMLPropertyMapping.objects.all()
    serializer_class = SAMLPropertyMappingSerializer
    filterset_class = SAMLPropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
