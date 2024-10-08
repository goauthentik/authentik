"""OAuth source property mappings API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.oauth.models import OAuthSourcePropertyMapping


class OAuthSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """OAuthSourcePropertyMapping Serializer"""

    class Meta(PropertyMappingSerializer.Meta):
        model = OAuthSourcePropertyMapping


class OAuthSourcePropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for OAuthSourcePropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = OAuthSourcePropertyMapping


class OAuthSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """OAuthSourcePropertyMapping Viewset"""

    queryset = OAuthSourcePropertyMapping.objects.all()
    serializer_class = OAuthSourcePropertyMappingSerializer
    filterset_class = OAuthSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
