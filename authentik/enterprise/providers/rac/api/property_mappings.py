"""RAC Provider API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import JSONDictField
from authentik.enterprise.providers.rac.models import RACPropertyMapping


class RACPropertyMappingSerializer(PropertyMappingSerializer):
    """RACPropertyMapping Serializer"""

    static_settings = JSONDictField()

    class Meta:
        model = RACPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + ["static_settings"]


class RACPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """RACPropertyMapping Viewset"""

    queryset = RACPropertyMapping.objects.all()
    serializer_class = RACPropertyMappingSerializer
    search_fields = ["name"]
    ordering = ["name"]
