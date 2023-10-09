"""authentik Proxy app"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProviderProxyConfig(ManagedAppConfig):
    """authentik proxy app"""

    name = "authentik.providers.proxy"
    label = "authentik_providers_proxy"
    verbose_name = "authentik Providers.Proxy"
    default = True

    def reconcile_load_providers_proxy_signals(self):
        """Load proxy signals"""
        self.import_module("authentik.providers.proxy.signals")
