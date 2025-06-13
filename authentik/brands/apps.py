"""authentik brands app"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikBrandsConfig(ManagedAppConfig):
    """authentik Brand app"""

    name = "authentik.brands"
    label = "authentik_brands"
    verbose_name = "authentik Brands"
    default = True
    mountpoints = {
        "authentik.brands.urls_root": "",
    }
    default = True
