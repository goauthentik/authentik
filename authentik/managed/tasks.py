"""managed tasks"""
from glob import glob

from django.core.cache import cache
from django.db import DatabaseError

from authentik.core.tasks import CELERY_APP
from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.lib.config import CONFIG
from authentik.managed.config_files import ConfigFile
from authentik.managed.manager import ObjectManager


@CELERY_APP.task(bind=True, base=MonitoredTask)
def managed_reconcile(self: MonitoredTask):
    """Run ObjectManager to ensure objects are up-to-date"""
    try:
        ObjectManager().run()
        self.set_status(
            TaskResult(TaskResultStatus.SUCCESSFUL, ["Successfully updated managed models."])
        )
    except DatabaseError as exc:
        self.set_status(TaskResult(TaskResultStatus.WARNING, [str(exc)]))


@CELERY_APP.task(bind=True, base=MonitoredTask)
def config_file_discovery(self: MonitoredTask):
    """Find and load configuration files"""
    new_count = 0
    total_count = 0
    for file in glob(f"{CONFIG.y('config_file_dir')}/**.akconf"):
        total_count += 1
        if cache.get(f"config_file_{file}", None):
            continue
        ConfigFile(file).save()
        new_count += 1
    self.set_status(
        TaskResult(
            TaskResultStatus.SUCCESSFUL,
            [f"Found {new_count} new files and {total_count} total files found."],
        )
    )
