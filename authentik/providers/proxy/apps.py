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

        def snapshot(provider: ProxyProvider):
            columns = [f.value_from_object(provider) for f in ProxyProvider._meta.concrete_fields]
            return columns + sorted(provider.property_mappings.values_list("pk", flat=True))

        for pk in ProxyProvider.objects.order_by("pk").values_list("pk", flat=True):
            with transaction.atomic():
                provider = (
                    ProxyProvider.objects.select_for_update(no_key=True).filter(pk=pk).first()
                )
                if provider is None:
                    continue
                before = snapshot(provider)
                provider.set_oauth_defaults()
                if snapshot(provider) != before:
                    provider.save()
