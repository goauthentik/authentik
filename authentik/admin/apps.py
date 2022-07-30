"""authentik admin app config"""
from importlib import import_module

from django.apps import AppConfig
from prometheus_client import Gauge, Info

PROM_INFO = Info("authentik_version", "Currently running authentik version")
GAUGE_WORKERS = Gauge("authentik_admin_workers", "Currently connected workers")


class AuthentikAdminConfig(AppConfig):
    """authentik admin app config"""

    name = "authentik.admin"
    label = "authentik_admin"
    verbose_name = "authentik Admin"

    def ready(self):
        import_module("authentik.admin.signals")
