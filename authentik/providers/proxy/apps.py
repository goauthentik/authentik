"""authentik Proxy app"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikProviderProxyConfig(AppConfig):
    """authentik proxy app"""

    name = "authentik.providers.proxy"
    label = "authentik_providers_proxy"
    verbose_name = "authentik Providers.Proxy"

    def ready(self) -> None:
        import_module("authentik.providers.proxy.managed")
