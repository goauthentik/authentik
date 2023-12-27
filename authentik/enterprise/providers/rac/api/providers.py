"""RAC Provider API Views"""
from rest_framework.fields import CharField, ListField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.providers.rac.models import RACProvider


class RACProviderSerializer(ProviderSerializer):
    """RACProvider Serializer"""

    outpost_set = ListField(child=CharField(), read_only=True, source="outpost_set.all")

    class Meta:
        model = RACProvider
        fields = ProviderSerializer.Meta.fields + ["settings", "outpost_set"]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class RACProviderViewSet(UsedByMixin, ModelViewSet):
    """RACProvider Viewset"""

    queryset = RACProvider.objects.all()
    serializer_class = RACProviderSerializer
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
    }
    search_fields = ["name"]
    ordering = ["name"]
