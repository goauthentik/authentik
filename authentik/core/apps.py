"""authentik core app config"""

from django.conf import settings

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikCoreConfig(ManagedAppConfig):
    """authentik core app config"""

    name = "authentik.core"
    label = "authentik_core"
    verbose_name = "authentik Core"
    mountpoint = ""
    default = True

    @ManagedAppConfig.reconcile_global
    def debug_worker_hook(self):
        """Dispatch startup tasks inline when debugging"""
        if settings.DEBUG:
            from authentik.root.celery import worker_ready_hook

            worker_ready_hook()

    @ManagedAppConfig.reconcile_tenant
    def source_inbuilt(self):
        """Reconcile inbuilt source"""
        from authentik.core.models import Source

        Source.objects.update_or_create(
            defaults={
                "name": "authentik Built-in",
                "slug": "authentik-built-in",
            },
            managed=Source.MANAGED_INBUILT,
        )
