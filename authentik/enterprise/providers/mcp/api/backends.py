"""MCP backend API Views"""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import Application
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.mcp.models import TOOL_SEPARATOR, MCPBackend
from authentik.providers.oauth2.models import OAuth2Provider


class MCPBackendSerializer(EnterpriseRequiredMixin, ModelSerializer):
    """MCPBackend Serializer"""

    def validate_slug(self, slug: str) -> str:
        if TOOL_SEPARATOR in slug:
            raise ValidationError(_("Slug may not contain '{s}'.").format(s=TOOL_SEPARATOR))
        return slug

    def validate_token_application(self, application: Application | None) -> Application | None:
        if application and not isinstance(application.get_provider(), OAuth2Provider):
            raise ValidationError(_("Application must use an OAuth2 provider."))
        return application

    class Meta:
        model = MCPBackend
        fields = [
            "pbm_uuid",
            "gateway",
            "name",
            "slug",
            "url",
            "token_application",
            "token_validity",
            "policy_engine_mode",
        ]


class MCPBackendViewSet(UsedByMixin, ModelViewSet):
    """MCPBackend Viewset"""

    queryset = MCPBackend.objects.all().select_related("gateway")
    serializer_class = MCPBackendSerializer
    filterset_fields = ["gateway"]
    search_fields = ["name", "slug"]
    ordering = ["name"]
