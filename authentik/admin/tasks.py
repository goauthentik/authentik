"""authentik admin tasks"""

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq import actor
from packaging.version import parse
from requests import RequestException
from structlog.stdlib import get_logger

from authentik import __version__, get_build_hash
from authentik.admin.apps import PROM_INFO
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.lib.utils.http import get_http_session
from authentik.tasks.models import Task

LOGGER = get_logger()
VERSION_NULL = "0.0.0"
VERSION_CACHE_KEY = "authentik_latest_version"
VERSION_CACHE_TIMEOUT = 8 * 60 * 60  # 8 hours
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


@actor(description=_("Update latest version info."))
def update_latest_version():
    self: Task = CurrentTask.get_task()
    if CONFIG.get_bool("disable_update_check"):
        cache.set(VERSION_CACHE_KEY, VERSION_NULL, VERSION_CACHE_TIMEOUT)
        self.info("Version check disabled.")
        return
    try:
        response = get_http_session().get(
            "https://version.goauthentik.io/version.json",
        )
        response.raise_for_status()
        data = response.json()
        upstream_version = data.get("stable", {}).get("version")
        cache.set(VERSION_CACHE_KEY, upstream_version, VERSION_CACHE_TIMEOUT)
        self.info("Successfully updated latest Version")
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
            Event.new(
                EventAction.UPDATE_AVAILABLE,
                message=_(
                    "New version {version} available!".format(
                        version=upstream_version,
                    )
                ),
                new_version=upstream_version,
                changelog=data.get("stable", {}).get("changelog_url"),
            ).save()
    except (RequestException, IndexError) as exc:
        cache.set(VERSION_CACHE_KEY, VERSION_NULL, VERSION_CACHE_TIMEOUT)
        raise exc


_set_prom_info()
