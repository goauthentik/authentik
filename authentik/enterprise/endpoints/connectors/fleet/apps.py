"""authentik endpoints app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEnterpriseEndpointsConnectorFleetAppConfig(ManagedAppConfig):
    """authentik endpoints app config"""

    name = "authentik.enterprise.endpoints.connectors.fleet"
    label = "authentik_endpoints_connectors_fleet"
    verbose_name = "authentik Enterprise.Endpoints.Connectors.Fleet"
    default = True
