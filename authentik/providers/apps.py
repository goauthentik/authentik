"""authentik providers app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProvidersConfig(ManagedAppConfig):
    """authentik providers app config"""

    name = "authentik.providers"
    label = "authentik_providers"
    verbose_name = "authentik Providers"
    default = True
