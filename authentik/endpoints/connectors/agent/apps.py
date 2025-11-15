"""authentik endpoints app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEndpointsConnectorAgentAppConfig(ManagedAppConfig):
    """authentik endpoints app config"""

    name = "authentik.endpoints.connectors.agent"
    label = "authentik_endpoints_connectors_agent"
    verbose_name = "authentik Endpoints.Connectors.Agent"
    default = True
    mountpoints = {
        "authentik.endpoints.connectors.agent.urls": "endpoint/agent/",
        "authentik.endpoints.connectors.agent.urls_root": "",
    }
