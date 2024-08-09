"""Kerberos Property Mapping API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.kerberos.models import KerberosPropertyMapping


class KerberosPropertyMappingSerializer(PropertyMappingSerializer):
    """Kerberos PropertyMapping Serializer"""

    class Meta(PropertyMappingSerializer.Meta):
        model = KerberosPropertyMapping


class KerberosPropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for KerberosPropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = KerberosPropertyMapping


class KerberosPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """Kerberos PropertyMapping Viewset"""

    queryset = KerberosPropertyMapping.objects.all()
    serializer_class = KerberosPropertyMappingSerializer
    filterset_class = KerberosPropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
