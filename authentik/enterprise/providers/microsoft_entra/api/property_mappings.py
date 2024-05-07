"""microsoft Property mappings API Views"""

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProviderMapping


class MicrosoftProviderMappingSerializer(PropertyMappingSerializer):
    """MicrosoftProviderMapping Serializer"""

    class Meta:
        model = MicrosoftEntraProviderMapping
        fields = PropertyMappingSerializer.Meta.fields


class MicrosoftProviderMappingFilter(FilterSet):
    """Filter for MicrosoftProviderMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = MicrosoftEntraProviderMapping
        fields = "__all__"


class MicrosoftProviderMappingViewSet(UsedByMixin, ModelViewSet):
    """MicrosoftProviderMapping Viewset"""

    queryset = MicrosoftEntraProviderMapping.objects.all()
    serializer_class = MicrosoftProviderMappingSerializer
    filterset_class = MicrosoftProviderMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
