"""Apple Platform SSO Provider API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.apple_psso.models import ApplePlatformSSOProvider


class ApplePlatformSSOProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """ApplePlatformSSOProvider Serializer"""

    class Meta:
        model = ApplePlatformSSOProvider
        fields = [
            "pk",
            "name",
        ]
        extra_kwargs = {}


class ApplePlatformSSOProviderViewSet(UsedByMixin, ModelViewSet):
    """ApplePlatformSSOProvider Viewset"""

    queryset = ApplePlatformSSOProvider.objects.all()
    serializer_class = ApplePlatformSSOProviderSerializer
    filterset_fields = [
        "name",
    ]
    search_fields = ["name"]
    ordering = ["name"]
