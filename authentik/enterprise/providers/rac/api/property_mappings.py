"""RAC Provider API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.rac.models import RACPropertyMapping


class RACPropertyMappingSerializer(PropertyMappingSerializer):
    """RACPropertyMapping Serializer"""

    class Meta:
        model = RACPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + []


class RACPropertyMappingViewSet(UsedByMixin, ModelViewSet):
    """RACPropertyMapping Viewset"""

    queryset = RACPropertyMapping.objects.all()
    serializer_class = RACPropertyMappingSerializer
    search_fields = ["name"]
    ordering = ["name"]
