"""authentik Proxy app"""
from authentik.blueprints.manager import ManagedAppConfig


class AuthentikProviderProxyConfig(ManagedAppConfig):
    """authentik proxy app"""

    name = "authentik.providers.proxy"
    label = "authentik_providers_proxy"
    verbose_name = "authentik Providers.Proxy"
    default = True

    def reconcile_trigger_proxy_set_defaults(self):
        """Trigger set_defaults task"""
        from authentik.providers.proxy.tasks import proxy_set_defaults

        proxy_set_defaults.delay()
