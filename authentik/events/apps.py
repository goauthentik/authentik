"""authentik events app"""

from prometheus_client import Gauge, Histogram

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.config import CONFIG, ENV_PREFIX
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec

# TODO: Deprecated metric - remove in 2024.2 or later
GAUGE_TASKS = Gauge(
    "authentik_system_tasks",
    "System tasks and their status",
    ["tenant", "task_name", "task_uid", "status"],
)

SYSTEM_TASK_TIME = Histogram(
    "authentik_system_tasks_time_seconds",
    "Runtime of system tasks",
    ["tenant", "task_name", "task_uid"],
)
SYSTEM_TASK_STATUS = Gauge(
    "authentik_system_tasks_status",
    "System task status",
    ["tenant", "task_name", "task_uid", "status"],
)


class AuthentikEventsConfig(ManagedAppConfig):
    """authentik events app"""

    name = "authentik.events"
    label = "authentik_events"
    verbose_name = "authentik Events"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.events.tasks import notification_cleanup

        return [
            ScheduleSpec(
                actor=notification_cleanup,
                crontab=f"{fqdn_rand('notification_cleanup')} */8 * * *",
            ),
        ]

    @ManagedAppConfig.reconcile_global
    def check_deprecations(self):
        """Check for config deprecations"""
        from authentik.events.models import Event, EventAction

        for key_replace, msg in CONFIG.deprecations.items():
            key, replace = key_replace
            key_env = f"{ENV_PREFIX}_{key.replace('.', '__')}".upper()
            replace_env = f"{ENV_PREFIX}_{replace.replace('.', '__')}".upper()
            if Event.objects.filter(
                action=EventAction.CONFIGURATION_ERROR, context__deprecated_option=key
            ).exists():
                continue
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                deprecated_option=key,
                deprecated_env=key_env,
                replacement_option=replace,
                replacement_env=replace_env,
                message=msg,
            ).save()
