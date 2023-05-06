"""authentik interfaces app config"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikInterfacesConfig(ManagedAppConfig):
    """authentik interfaces app config"""

    name = "authentik.interfaces"
    label = "authentik_interfaces"
    verbose_name = "authentik Interfaces"
    mountpoint = "if/"
    default = True
