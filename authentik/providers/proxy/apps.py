"""authentik Proxy app"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProviderProxyConfig(ManagedAppConfig):
    """authentik proxy app"""

    name = "authentik.providers.proxy"
    label = "authentik_providers_proxy"
    verbose_name = "authentik Providers.Proxy"
    default = True

    @ManagedAppConfig.reconcile_tenant
    def proxy_set_defaults(self):
        from authentik.providers.proxy.tasks import proxy_set_defaults

        proxy_set_defaults.send()
