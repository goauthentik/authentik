"""Apple Platform SSO Provider API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.endpoints.apple_psso.models import ApplePlatformSSOConnector


class ApplePlatformSSOConnectorSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """ApplePlatformSSOConnector Serializer"""

    class Meta:
        model = ApplePlatformSSOConnector
        fields = [
            "pk",
            "name",
        ]
        extra_kwargs = {}


class ApplePlatformSSOConnectorViewSet(UsedByMixin, ModelViewSet):
    """ApplePlatformSSOConnector Viewset"""

    queryset = ApplePlatformSSOConnector.objects.all()
    serializer_class = ApplePlatformSSOConnectorSerializer
    filterset_fields = [
        "name",
    ]
    search_fields = ["name"]
    ordering = ["name"]
