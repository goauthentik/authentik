"""RadiusProvider API Views"""
from rest_framework.fields import CharField, ListField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.radius.models import RadiusProvider


class RadiusProviderSerializer(ProviderSerializer):
    """RadiusProvider Serializer"""

    outpost_set = ListField(child=CharField(), read_only=True, source="outpost_set.all")

    class Meta:
        model = RadiusProvider
        fields = ProviderSerializer.Meta.fields + [
            "client_networks",
            # Shared secret is not a write-only field, as
            # an admin might have to view it
            "shared_secret",
            "outpost_set",
            "mfa_support",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class RadiusProviderViewSet(UsedByMixin, ModelViewSet):
    """RadiusProvider Viewset"""

    queryset = RadiusProvider.objects.all()
    serializer_class = RadiusProviderSerializer
    ordering = ["name"]
    search_fields = ["name", "client_networks"]
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
        "authorization_flow__slug": ["iexact"],
        "client_networks": ["iexact"],
    }


class RadiusOutpostConfigSerializer(ModelSerializer):
    """RadiusProvider Serializer"""

    application_slug = CharField(source="application.slug")
    auth_flow_slug = CharField(source="authorization_flow.slug")

    class Meta:
        model = RadiusProvider
        fields = [
            "pk",
            "name",
            "application_slug",
            "auth_flow_slug",
            "client_networks",
            "shared_secret",
            "mfa_support",
        ]


class RadiusOutpostConfigViewSet(ReadOnlyModelViewSet):
    """RadiusProvider Viewset"""

    queryset = RadiusProvider.objects.filter(application__isnull=False)
    serializer_class = RadiusOutpostConfigSerializer
    ordering = ["name"]
    search_fields = ["name"]
    filterset_fields = ["name"]
