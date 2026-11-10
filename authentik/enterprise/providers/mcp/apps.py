"""MCP gateway provider app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderMCPConfig(EnterpriseConfig):
    """authentik enterprise MCP gateway provider app config"""

    name = "authentik.enterprise.providers.mcp"
    label = "authentik_providers_mcp"
    verbose_name = "authentik Enterprise.Providers.MCP"
    default = True
    mountpoint = ""
