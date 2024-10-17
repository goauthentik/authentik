"""authentik analytics app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikAdminConfig(ManagedAppConfig):
    """authentik analytics app config"""

    name = "authentik.analytics"
    label = "authentik_analytics"
    verbose_name = "authentik Analytics"
    default = True
