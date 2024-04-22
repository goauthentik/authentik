"""google Property mappings API Views"""

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.google.models import GoogleProviderMapping


class GoogleProviderMappingSerializer(PropertyMappingSerializer):
    """GoogleProviderMapping Serializer"""

    class Meta:
        model = GoogleProviderMapping
        fields = PropertyMappingSerializer.Meta.fields


class GoogleProviderMappingFilter(FilterSet):
    """Filter for GoogleProviderMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = GoogleProviderMapping
        fields = "__all__"


class GoogleProviderMappingViewSet(UsedByMixin, ModelViewSet):
    """GoogleProviderMapping Viewset"""

    queryset = GoogleProviderMapping.objects.all()
    serializer_class = GoogleProviderMappingSerializer
    filterset_class = GoogleProviderMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
