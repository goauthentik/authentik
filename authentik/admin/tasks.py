"""authentik admin tasks"""
from django.core.cache import cache
from packaging.version import parse
from requests import RequestException, get
from structlog.stdlib import get_logger

from authentik import __version__
from authentik.events.models import Event, EventAction
from authentik.lib.tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()
VERSION_CACHE_KEY = "authentik_latest_version"
VERSION_CACHE_TIMEOUT = 2 * 60 * 60  # 2 hours


@CELERY_APP.task(bind=True, base=MonitoredTask)
def update_latest_version(self: MonitoredTask):
    """Update latest version info"""
    try:
        response = get("https://api.github.com/repos/beryju/authentik/releases/latest")
        response.raise_for_status()
        data = response.json()
        tag_name = data.get("tag_name")
        upstream_version = tag_name.split("/")[1]
        cache.set(VERSION_CACHE_KEY, upstream_version, VERSION_CACHE_TIMEOUT)
        self.set_status(
            TaskResult(
                TaskResultStatus.SUCCESSFUL, ["Successfully updated latest Version"]
            )
        )
        # Check if upstream version is newer than what we're running,
        # and if no event exists yet, create one.
        local_version = parse(__version__)
        if local_version < parse(upstream_version):
            # Event has already been created, don't create duplicate
            if Event.objects.filter(
                action=EventAction.UPDATE_AVAILABLE,
                context__new_version=upstream_version,
            ).exists():
                return
            Event.new(EventAction.UPDATE_AVAILABLE, new_version=upstream_version).save()
    except (RequestException, IndexError) as exc:
        cache.set(VERSION_CACHE_KEY, "0.0.0", VERSION_CACHE_TIMEOUT)
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
