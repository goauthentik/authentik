"""Source API Views"""
from django_filters.filters import AllValuesMultipleFilter
from django_filters.filterset import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.ldap.models import LDAPPropertyMapping


class LDAPPropertyMappingSerializer(PropertyMappingSerializer):
    """LDAP PropertyMapping Serializer"""

    class Meta:
        model = LDAPPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + [
            "object_field",
        ]


class LDAPPropertyMappingFilter(FilterSet):
    """Filter for LDAPPropertyMapping"""

    managed = extend_schema_field(OpenApiTypes.STR)(AllValuesMultipleFilter(field_name="managed"))

    class Meta:
        model = LDAPPropertyMapping
        fields = "__all__"


class LDAPPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """LDAP PropertyMapping Viewset"""

    queryset = LDAPPropertyMapping.objects.all()
    serializer_class = LDAPPropertyMappingSerializer
    filterset_class = LDAPPropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
