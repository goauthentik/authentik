"""OAuth source property mappings API"""

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.oauth.models import OAuthSourcePropertyMapping


class OAuthSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """OAuthSourcePropertyMapping Serializer"""

    class Meta:
        model = OAuthSourcePropertyMapping
        fields = PropertyMappingSerializer.Meta.fields


class OAuthSourcePropertyMappingFilter(FilterSet):
    """Filter for OAuthSourcePropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = OAuthSourcePropertyMapping
        fields = "__all__"


class OAuthSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """OAuthSourcePropertyMapping Viewset"""

    queryset = OAuthSourcePropertyMapping.objects.all()
    serializer_class = OAuthSourcePropertyMappingSerializer
    filterset_class = OAuthSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
