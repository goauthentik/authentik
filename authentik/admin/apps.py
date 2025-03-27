"""authentik admin app config"""

from prometheus_client import Info

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand

PROM_INFO = Info("authentik_version", "Currently running authentik version")


class AuthentikAdminConfig(ManagedAppConfig):
    """authentik admin app config"""

    name = "authentik.admin"
    label = "authentik_admin"
    verbose_name = "authentik Admin"
    default = True

    def get_tenant_schedules(self):
        return [
            {
                "actor_name": "authentik.admin.tasks.update_latest_version",
                "crontab": f"{fqdn_rand('admin_latest_version')} * * * *",
            },
        ]
