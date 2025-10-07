"""authentik endpoints app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEnterpriseEndpointsConnectorAgentAppConfig(ManagedAppConfig):
    """authentik endpoints app config"""

    name = "authentik.enterprise.endpoints.connectors.agent"
    label = "authentik_endpoints_connectors_agent"
    verbose_name = "authentik Enterprise.Endpoints.Connectors.Agent"
    default = True
    mountpoints = {
        "authentik.enterprise.endpoints.connectors.agent.urls": "endpoint/agent/",
        "authentik.enterprise.endpoints.connectors.agent.urls_root": "",
    }
