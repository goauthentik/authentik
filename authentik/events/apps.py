"""authentik events app"""

from celery.schedules import crontab
from prometheus_client import Gauge, Histogram

from authentik.blueprints.apps import ManagedAppConfig
from authentik.common.config import CONFIG, ENV_PREFIX
from authentik.lib.utils.reflection import path_to_class
from authentik.root.celery import CELERY_APP

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

    @ManagedAppConfig.reconcile_tenant
    def prefill_tasks(self):
        """Prefill tasks"""
        from authentik.events.models import SystemTask
        from authentik.events.system_tasks import _prefill_tasks

        for task in _prefill_tasks:
            if SystemTask.objects.filter(name=task.name).exists():
                continue
            task.save()
            self.logger.debug("prefilled task", task_name=task.name)

    @ManagedAppConfig.reconcile_tenant
    def run_scheduled_tasks(self):
        """Run schedule tasks which are behind schedule (only applies
        to tasks of which we keep metrics)"""
        from authentik.events.models import TaskStatus
        from authentik.events.system_tasks import SystemTask as CelerySystemTask

        for task in CELERY_APP.conf["beat_schedule"].values():
            schedule = task["schedule"]
            if not isinstance(schedule, crontab):
                continue
            task_class: CelerySystemTask = path_to_class(task["task"])
            if not isinstance(task_class, CelerySystemTask):
                continue
            db_task = task_class.db()
            if not db_task:
                continue
            due, _ = schedule.is_due(db_task.finish_timestamp)
            if due or db_task.status == TaskStatus.UNKNOWN:
                self.logger.debug("Running past-due scheduled task", task=task["task"])
                task_class.apply_async(
                    args=task.get("args", None),
                    kwargs=task.get("kwargs", None),
                    **task.get("options", {}),
                )
