"""passbook admin tasks"""
from django.core.cache import cache
from requests import RequestException, get
from structlog import get_logger

from passbook.lib.tasks import MonitoredTask, TaskResult, TaskResultStatus
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()
VERSION_CACHE_KEY = "passbook_latest_version"
VERSION_CACHE_TIMEOUT = 2 * 60 * 60  # 2 hours


@CELERY_APP.task(bind=True, base=MonitoredTask)
def update_latest_version(self: MonitoredTask):
    """Update latest version info"""
    try:
        data = get(
            "https://api.github.com/repos/beryju/passbook/releases/latest"
        ).json()
        tag_name = data.get("tag_name")
        cache.set(VERSION_CACHE_KEY, tag_name.split("/")[1], VERSION_CACHE_TIMEOUT)
        self.set_status(
            TaskResult(
                TaskResultStatus.SUCCESSFUL, ["Successfully updated latest Version"]
            )
        )
    except (RequestException, IndexError) as exc:
        cache.set(VERSION_CACHE_KEY, "0.0.0", VERSION_CACHE_TIMEOUT)
        self.set_status(TaskResult(TaskResultStatus.ERROR, [str(exc)]))
