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

    @ManagedAppConfig.reconcile_global
    def clear_update_notifications(self):
        """Clear update notifications on startup if the notification was for the version
        we're running now."""
        from packaging.version import parse

        from authentik.admin.tasks import LOCAL_VERSION
        from authentik.events.models import EventAction, Notification

        for notification in Notification.objects.filter(event__action=EventAction.UPDATE_AVAILABLE):
            if "new_version" not in notification.event.context:
                continue
            notification_version = notification.event.context["new_version"]
            if LOCAL_VERSION >= parse(notification_version):
                notification.delete()

    @property
    def global_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.admin.tasks import update_latest_version

        return [
            ScheduleSpec(
                actor_name=update_latest_version.actor_name,
                crontab=f"{fqdn_rand('admin_latest_version')} * * * *",
            ),
        ]
