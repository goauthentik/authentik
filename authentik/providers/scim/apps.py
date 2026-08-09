"""authentik SCIM Provider app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProviderSCIMConfig(ManagedAppConfig):
    """authentik SCIM Provider app config"""

    name = "authentik.providers.scim"
    label = "authentik_providers_scim"
    verbose_name = "authentik Providers.SCIM"
    default = True
