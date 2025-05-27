"""authentik admin app config"""

from prometheus_client import Info

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.lib import ScheduleSpec

PROM_INFO = Info("authentik_version", "Currently running authentik version")


class AuthentikAdminConfig(ManagedAppConfig):
    """authentik admin app config"""

    name = "authentik.admin"
    label = "authentik_admin"
    verbose_name = "authentik Admin"
    default = True

    @ManagedAppConfig.reconcile_tenant
    def clear_update_notifications(self):
        from authentik.admin.tasks import clear_update_notifications

        clear_update_notifications.send()

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        return [
            ScheduleSpec(
                actor_name="authentik.admin.tasks.update_latest_version",
                crontab=f"{fqdn_rand('admin_latest_version')} * * * *",
            ),
        ]
