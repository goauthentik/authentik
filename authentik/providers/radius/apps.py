"""authentik radius provider app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProviderRadiusConfig(ManagedAppConfig):
    """authentik radius provider app config"""

    name = "authentik.providers.radius"
    label = "authentik_providers_radius"
    verbose_name = "authentik Providers.Radius"
    default = True
