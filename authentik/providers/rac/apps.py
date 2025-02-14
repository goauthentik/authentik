"""RAC app config"""

from django.apps import AppConfig


class AuthentikProviderRAC(AppConfig):
    """authentik rac app config"""

    name = "authentik.providers.rac"
    label = "authentik_providers_rac"
    verbose_name = "authentik Providers.RAC"
    default = True
    mountpoint = ""
    ws_mountpoint = "authentik.providers.rac.urls"
