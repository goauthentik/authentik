"""authentik endpoints app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseEndpointsConnectorFleetAppConfig(EnterpriseConfig):
    """authentik endpoints app config"""

    name = "authentik.enterprise.endpoints.connectors.fleet"
    label = "authentik_endpoints_connectors_fleet"
    verbose_name = "authentik Enterprise.Endpoints.Connectors.Fleet"
    default = True
