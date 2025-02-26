"""google Property mappings API Views"""

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProviderMapping


class GoogleWorkspaceProviderMappingSerializer(PropertyMappingSerializer):
    """GoogleWorkspaceProviderMapping Serializer"""

    class Meta:
        model = GoogleWorkspaceProviderMapping
        fields = PropertyMappingSerializer.Meta.fields


class GoogleWorkspaceProviderMappingFilter(FilterSet):
    """Filter for GoogleWorkspaceProviderMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = GoogleWorkspaceProviderMapping
        fields = "__all__"


class GoogleWorkspaceProviderMappingViewSet(UsedByMixin, ModelViewSet):
    """GoogleWorkspaceProviderMapping Viewset"""

    queryset = GoogleWorkspaceProviderMapping.objects.all()
    serializer_class = GoogleWorkspaceProviderMappingSerializer
    filterset_class = GoogleWorkspaceProviderMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
