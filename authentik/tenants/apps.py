"""authentik tenants app"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikTenantsConfig(ManagedAppConfig):
    """Retained so that migrations depending on this app's history keep resolving.

    The multi-tenancy feature was removed in 2026.11; the tables are dropped in a
    later release.
    """

    default = True
    name = "authentik.tenants"
    label = "authentik_tenants"
    verbose_name = "authentik Tenants"
