"""authentik endpoints app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEndpointsConnectorAgentAppConfig(ManagedAppConfig):
    """authentik endpoints app config"""

    name = "authentik.endpoints.connectors.agent"
    label = "authentik_endpoints_connectors_agent"
    verbose_name = "authentik Endpoints.Connectors.Agent"
    default = True

    def import_related(self):
        from authentik.endpoints.connectors.agent.models import AgentConnector

        _ = AgentConnector().stage
        return super().import_related()
