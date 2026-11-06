"""authentik Proxy app"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikProviderProxyConfig(ManagedAppConfig):
    """authentik proxy app"""

    name = "authentik.providers.proxy"
    label = "authentik_providers_proxy"
    verbose_name = "authentik Providers.Proxy"
    default = True

    @ManagedAppConfig.reconcile
    def proxy_set_defaults(self):
        from django.db import transaction

        from authentik.providers.proxy.models import ProxyProvider

        # TODO: figure out if this can be in pre_save + post_save signals
        with transaction.atomic():
            for provider in ProxyProvider.objects.all().select_for_update():
                provider.set_oauth_defaults()
                provider.save()
