"""authentik admin app config"""
from prometheus_client import Gauge, Info

from authentik.blueprints.manager import ManagedAppConfig

PROM_INFO = Info("authentik_version", "Currently running authentik version")
GAUGE_WORKERS = Gauge("authentik_admin_workers", "Currently connected workers")


class AuthentikAdminConfig(ManagedAppConfig):
    """authentik admin app config"""

    name = "authentik.admin"
    label = "authentik_admin"
    verbose_name = "authentik Admin"
    default = True

    def reconcile_load_admin_signals(self):
        """Load admin signals"""
        self.import_module("authentik.admin.signals")
