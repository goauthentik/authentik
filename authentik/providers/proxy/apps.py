"""authentik Proxy app"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProviderProxyConfig(ManagedAppConfig):
    """authentik proxy app"""

    name = "authentik.providers.proxy"
    label = "authentik_providers_proxy"
    verbose_name = "authentik Providers.Proxy"
    default = True

    startup_tasks_all_tenants = ("authentik.providers.proxy.tasks.proxy_set_defaults",)
