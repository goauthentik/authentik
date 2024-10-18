"""Kerberos Property Mapping API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.kerberos.models import KerberosSourcePropertyMapping


class KerberosSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """Kerberos PropertyMapping Serializer"""

    class Meta(PropertyMappingSerializer.Meta):
        model = KerberosSourcePropertyMapping


class KerberosSourcePropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for KerberosSourcePropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = KerberosSourcePropertyMapping


class KerberosSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """KerberosSource PropertyMapping Viewset"""

    queryset = KerberosSourcePropertyMapping.objects.all()
    serializer_class = KerberosSourcePropertyMappingSerializer
    filterset_class = KerberosSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
