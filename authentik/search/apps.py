"""Search app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSearchConfig(ManagedAppConfig):
    """Search app config"""

    name = "authentik.search"
    label = "authentik_search"
    verbose_name = "authentik Search"
    default = True
