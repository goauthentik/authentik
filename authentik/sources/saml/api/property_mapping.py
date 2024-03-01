"""SAML source property mappings API"""

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.saml.models import SAMLSourcePropertyMapping


class SAMLSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """SAMLSourcePropertyMapping Serializer"""

    class Meta:
        model = SAMLSourcePropertyMapping
        fields = PropertyMappingSerializer.Meta.fields


class SAMLSourcePropertyMappingFilter(FilterSet):
    """Filter for SAMLSourcePropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = SAMLSourcePropertyMapping
        fields = "__all__"


class SAMLSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """SAMLSourcePropertyMapping Viewset"""

    queryset = SAMLSourcePropertyMapping.objects.all()
    serializer_class = SAMLSourcePropertyMappingSerializer
    filterset_class = SAMLSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
