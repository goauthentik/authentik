"""authentik endpoints app"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEndpointsConfig(ManagedAppConfig):
    """authentik Endpoints app"""

    name = "authentik.endpoints"
    label = "authentik_endpoints"
    verbose_name = "authentik Endpoints"
    default = True
