"""authentik Proxy app"""
from django.apps import AppConfig


class AuthentikProviderProxyConfig(AppConfig):
    """authentik proxy app"""

    name = "authentik.providers.proxy"
    label = "authentik_providers_proxy"
    verbose_name = "authentik Providers.Proxy"
