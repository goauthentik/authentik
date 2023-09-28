"""authentik admin tasks"""
import re

from django.core.cache import cache
from django.core.validators import URLValidator
from django.db import DatabaseError, InternalError, ProgrammingError
from packaging.version import parse
from requests import RequestException
from structlog.stdlib import get_logger

from authentik import __version__, get_build_hash
from authentik.admin.apps import PROM_INFO
from authentik.events.models import Event, EventAction, Notification
from authentik.events.monitored_tasks import (
    MonitoredTask,
    TaskResult,
    TaskResultStatus,
    prefill_task,
)
from authentik.lib.config import CONFIG
from authentik.lib.utils.http import get_http_session
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()
VERSION_CACHE_KEY = "authentik_latest_version"
VERSION_CACHE_TIMEOUT = 8 * 60 * 60  # 8 hours
# Chop of the first ^ because we want to search the entire string
URL_FINDER = URLValidator.regex.pattern[1:]
LOCAL_VERSION = parse(__version__)


def _set_prom_info():
    """Set prometheus info for version"""
    PROM_INFO.info(
        {
            "version": __version__,
            "latest": cache.get(VERSION_CACHE_KEY, ""),
            "build_hash": get_build_hash(),
        }
    )


@CELERY_APP.task(
    throws=(DatabaseError, ProgrammingError, InternalError),
)
def clear_update_notifications():
    """Clear update notifications on startup if the notification was for the version
    we're running now."""
    for notification in Notification.objects.filter(event__action=EventAction.UPDATE_AVAILABLE):
        if "new_version" not in notification.event.context:
            continue
        notification_version = notification.event.context["new_version"]
        if LOCAL_VERSION >= parse(notification_version):
            notification.delete()


@CELERY_APP.task(bind=True, base=MonitoredTask)
@prefill_task
def update_latest_version(self: MonitoredTask):
    """Update latest version info"""
    if CONFIG.get_bool("disable_update_check"):
        cache.set(VERSION_CACHE_KEY, "0.0.0", VERSION_CACHE_TIMEOUT)
        self.set_status(TaskResult(TaskResultStatus.WARNING, messages=["Version check disabled."]))
        return
    try:
        response = get_http_session().get(
            "https://version.goauthentik.io/version.json",
        )
        response.raise_for_status()
        data = response.json()
        upstream_version = data.get("stable", {}).get("version")
        cache.set(VERSION_CACHE_KEY, upstream_version, VERSION_CACHE_TIMEOUT)
        self.set_status(
            TaskResult(TaskResultStatus.SUCCESSFUL, ["Successfully updated latest Version"])
        )
        _set_prom_info()
        # Check if upstream version is newer than what we're running,
        # and if no event exists yet, create one.
        if LOCAL_VERSION < parse(upstream_version):
            # Event has already been created, don't create duplicate
            if Event.objects.filter(
                action=EventAction.UPDATE_AVAILABLE,
                context__new_version=upstream_version,
            ).exists():
                return
            event_dict = {"new_version": upstream_version}
            if match := re.search(URL_FINDER, data.get("stable", {}).get("changelog", "")):
                event_dict["message"] = f"Changelog: {match.group()}"
            Event.new(EventAction.UPDATE_AVAILABLE, **event_dict).save()
    except (RequestException, IndexError) as exc:
        cache.set(VERSION_CACHE_KEY, "0.0.0", VERSION_CACHE_TIMEOUT)
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))


_set_prom_info()
