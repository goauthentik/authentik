from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseEndpointsConnectorAgentAppConfig(EnterpriseConfig):

    name = "authentik.enterprise.endpoints.connectors.agent"
    label = "authentik_enterprise_endpoints_connectors_agent"
    verbose_name = "authentik Enterprise.Endpoints.Connectors.Agent"
    default = True
    mountpoints = {
        "authentik.enterprise.endpoints.connectors.agent.urls_root": "",
    }
