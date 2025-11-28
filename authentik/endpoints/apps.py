"""authentik endpoints app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEndpointsConfig(ManagedAppConfig):
    """authentik endpoints app config"""

    name = "authentik.endpoints"
    label = "authentik_endpoints"
    verbose_name = "authentik Endpoints"
    default = True
