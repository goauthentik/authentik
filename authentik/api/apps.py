"""authentik API AppConfig"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikAPIConfig(ManagedAppConfig):
    """authentik API Config"""

    name = "authentik.api"
    label = "authentik_api"
    verbose_name = "authentik API"
    default = True
    mountpoint = "api/"
