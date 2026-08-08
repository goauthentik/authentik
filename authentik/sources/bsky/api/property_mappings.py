from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.bsky.models import BskySourcePropertyMapping


class BskySourcePropertyMappingSerializer(PropertyMappingSerializer):
    class Meta(PropertyMappingSerializer.Meta):
        model = BskySourcePropertyMapping


class BskySourcePropertyMappingFilter(PropertyMappingFilterSet):
    class Meta(PropertyMappingFilterSet.Meta):
        model = BskySourcePropertyMapping


class BskySourcePropertyMappingViewSet(UsedByMixin, ModelViewSet[BskySourcePropertyMapping]):
    queryset = BskySourcePropertyMapping.objects.all()
    serializer_class = BskySourcePropertyMappingSerializer
    filterset_class = BskySourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
