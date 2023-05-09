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

    def reconcile_load_core_signals(self):
        """Load core signals"""
        self.import_module("authentik.core.signals")

    def reconcile_debug_worker_hook(self):
        """Dispatch startup tasks inline when debugging"""
        if settings.DEBUG:
            from authentik.root.celery import worker_ready_hook

            worker_ready_hook()

    def reconcile_source_inbuilt(self):
        """Reconcile inbuilt source"""
        from authentik.core.models import Source

        Source.objects.update_or_create(
            defaults={
                "name": "authentik Built-in",
                "slug": "authentik-built-in",
            },
            managed="goauthentik.io/sources/inbuilt",
        )
