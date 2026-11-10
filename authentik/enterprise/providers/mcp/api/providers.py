"""MCP gateway provider API Views"""

from django.urls import reverse
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.mcp.models import MCPGatewayProvider


class MCPGatewayProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """MCPGatewayProvider Serializer"""

    url = SerializerMethodField()

    def get_url(self, instance: MCPGatewayProvider) -> str | None:
        request: Request = self._context.get("request")
        if not request or not instance.backchannel_application:
            return None
        return request.build_absolute_uri(
            reverse(
                "authentik_providers_mcp:gateway",
                kwargs={"application_slug": instance.backchannel_application.slug},
            )
        )

    class Meta:
        model = MCPGatewayProvider
        fields = [
            "pk",
            "name",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "url",
        ]


class MCPGatewayProviderViewSet(UsedByMixin, ModelViewSet):
    """MCPGatewayProvider Viewset"""

    queryset = MCPGatewayProvider.objects.all().select_related("backchannel_application")
    serializer_class = MCPGatewayProviderSerializer
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
    }
    search_fields = ["name"]
    ordering = ["name"]
