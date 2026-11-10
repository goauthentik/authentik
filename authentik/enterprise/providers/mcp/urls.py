"""MCP gateway provider URLs"""

from django.urls import path

from authentik.enterprise.providers.mcp.api.backends import MCPBackendViewSet
from authentik.enterprise.providers.mcp.api.providers import MCPGatewayProviderViewSet
from authentik.enterprise.providers.mcp.views import GatewayView, ProtectedResourceMetadataView

urlpatterns = [
    path(
        "application/mcp/<slug:application_slug>/",
        GatewayView.as_view(),
        name="gateway",
    ),
    path(
        ".well-known/oauth-protected-resource/application/mcp/<slug:application_slug>/",
        ProtectedResourceMetadataView.as_view(),
        name="protected-resource-metadata",
    ),
]

api_urlpatterns = [
    ("providers/mcp", MCPGatewayProviderViewSet),
    ("providers/mcp_backends", MCPBackendViewSet),
]
