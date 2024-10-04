"""authentik brands app"""

from django.apps import AppConfig


class AuthentikBrandsConfig(AppConfig):
    """authentik Brand app"""

    name = "authentik.brands"
    label = "authentik_brands"
    verbose_name = "authentik Brands"
    mountpoints = {
        "authentik.brands.urls_root": "",
    }
