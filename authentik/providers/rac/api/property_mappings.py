"""RAC Provider API Views"""

from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.fields import CharField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import JSONDictField
from authentik.providers.rac.models import RACPropertyMapping


class RACPropertyMappingSerializer(PropertyMappingSerializer):
    """RACPropertyMapping Serializer"""

    static_settings = JSONDictField()
    expression = CharField(allow_blank=True, required=False)

    def validate_expression(self, expression: str) -> str:
        """Test Syntax"""
        if expression == "":
            return expression
        return super().validate_expression(expression)

    class Meta:
        model = RACPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + ["static_settings"]


class RACPropertyMappingFilter(FilterSet):
    """Filter for RACPropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = RACPropertyMapping
        fields = ["name", "managed"]


class RACPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """RACPropertyMapping Viewset"""

    queryset = RACPropertyMapping.objects.all()
    serializer_class = RACPropertyMappingSerializer
    search_fields = ["name"]
    ordering = ["name"]
    filterset_class = RACPropertyMappingFilter
