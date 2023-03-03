"""SCIM Provider API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.providers.scim.models import SCIMProvider


class SCIMProviderSerializer(ProviderSerializer):
    """SCIMProvider Serializer"""

    class Meta:
        model = SCIMProvider
        fields = [
            "pk",
            "name",
            "property_mappings",
            "component",
            "assigned_application_slug",
            "assigned_application_name",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "url",
            "token",
        ]
        extra_kwargs = {}


class SCIMProviderViewSet(UsedByMixin, ModelViewSet):
    """SCIMProvider Viewset"""

    queryset = SCIMProvider.objects.all()
    serializer_class = SCIMProviderSerializer
    filterset_fields = ["name", "authorization_flow", "url", "token"]
    search_fields = ["name", "url"]
    ordering = ["name", "url"]
