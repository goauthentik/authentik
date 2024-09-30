"""authentik admin app config"""

from prometheus_client import Gauge, Info

from authentik import get_build_hash, __version__
from authentik.blueprints.apps import ManagedAppConfig

from authentik.root.signals import startup

PROM_INFO = Info("authentik_version", "Currently running authentik version")
GAUGE_WORKERS = Gauge("authentik_admin_workers", "Currently connected workers")


class AuthentikAdminConfig(ManagedAppConfig):
    """authentik admin app config"""

    name = "authentik.admin"
    label = "authentik_admin"
    verbose_name = "authentik Admin"
    default = True

    def ready(self):
        startup.connect(self.create_new_version_history_entry, dispatch_uid=self.label)
        return super().ready()

    def create_new_version_history_entry(self, sender, **_):
        from authentik.admin.models import VersionHistory

        VersionHistory.create_new_entry(version=__version__, build=get_build_hash(""))
