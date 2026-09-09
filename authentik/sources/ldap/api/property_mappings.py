from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.ldap.models import (
    LDAPSourcePropertyMapping,
)


class LDAPSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """LDAP PropertyMapping Serializer"""

    class Meta:
        model = LDAPSourcePropertyMapping
        fields = PropertyMappingSerializer.Meta.fields


class LDAPSourcePropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for LDAPSourcePropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = LDAPSourcePropertyMapping


class LDAPSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """LDAP PropertyMapping Viewset"""

    queryset = LDAPSourcePropertyMapping.objects.all()
    serializer_class = LDAPSourcePropertyMappingSerializer
    filterset_class = LDAPSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
