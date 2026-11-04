"""Telegram source property mappings API"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.property_mappings import PropertyMappingFilterSet, PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.telegram.models import TelegramSourcePropertyMapping


class TelegramSourcePropertyMappingSerializer(PropertyMappingSerializer):
    """TelegramSourcePropertyMapping Serializer"""

    class Meta(PropertyMappingSerializer.Meta):
        model = TelegramSourcePropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + ["list_merge_mode"]


class TelegramSourcePropertyMappingFilter(PropertyMappingFilterSet):
    """Filter for TelegramSourcePropertyMapping"""

    class Meta(PropertyMappingFilterSet.Meta):
        model = TelegramSourcePropertyMapping


class TelegramSourcePropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """TelegramSourcePropertyMapping Viewset"""

    queryset = TelegramSourcePropertyMapping.objects.all()
    serializer_class = TelegramSourcePropertyMappingSerializer
    filterset_class = TelegramSourcePropertyMappingFilter
    search_fields = ["name"]
    ordering = ["name"]
