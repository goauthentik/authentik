"""MCP gateway provider models"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import Application, BackchannelProvider
from authentik.lib.models import SerializerModel
from authentik.lib.utils.time import timedelta_string_validator
from authentik.policies.models import PolicyBindingModel

# Separates the backend slug from the upstream tool name in gateway tool names. Only
# `[a-zA-Z0-9_-]` is used, as some MCP clients reject any other characters in tool names.
TOOL_SEPARATOR = "__"


class MCPGatewayProvider(BackchannelProvider):
    """Single MCP endpoint aggregating the tools of multiple backend MCP servers.

    Clients authenticate with access tokens issued by the OAuth2 provider of the
    application this gateway is a backchannel provider of."""

    @property
    def component(self) -> str:
        return "ak-provider-mcp-gateway-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.mcp.api.providers import MCPGatewayProviderSerializer

        return MCPGatewayProviderSerializer

    class Meta:
        verbose_name = _("MCP Gateway Provider")
        verbose_name_plural = _("MCP Gateway Providers")


class MCPBackend(SerializerModel, PolicyBindingModel):
    """Upstream MCP server whose tools are exposed through a gateway.

    Policies bound to a backend are evaluated for every tool, with
    `context["mcp"]` holding the tool name and (for calls) its arguments."""

    gateway = models.ForeignKey(
        MCPGatewayProvider, on_delete=models.CASCADE, related_name="backends"
    )
    name = models.TextField()
    slug = models.SlugField(
        help_text=_("Prefix for this backend's tools, as `<slug>__<tool>`."),
    )
    url = models.TextField(help_text=_("Streamable HTTP endpoint of the MCP server."))

    token_application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name="+",
        help_text=_(
            "Application with an OAuth2 provider used to issue a short-lived access token for "
            "the user on every call to this backend. Users must also have access to this "
            "application to use this backend's tools."
        ),
    )
    token_validity = models.TextField(
        default="minutes=5",
        validators=[timedelta_string_validator],
        help_text=_("Validity of access tokens issued for this backend."),
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.providers.mcp.api.backends import MCPBackendSerializer

        return MCPBackendSerializer

    def __str__(self) -> str:
        return f"MCP Backend {self.name}"

    class Meta:
        verbose_name = _("MCP Backend")
        verbose_name_plural = _("MCP Backends")
        unique_together = (("gateway", "slug"),)
