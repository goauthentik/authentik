"""authentik admin tasks"""

from enum import StrEnum

from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _
from dramatiq import actor
from packaging.version import parse
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from requests import RequestException
from structlog.stdlib import get_logger

from authentik import authentik_build_hash, authentik_version
from authentik.admin.apps import PROM_INFO
from authentik.core.api.utils import PassiveSerializer
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.lib.utils.http import get_http_session
from authentik.tasks.middleware import CurrentTask

LOGGER = get_logger()
VERSION_CACHE_KEY = "goauthentik.io/admin/latest_version"
VERSION_CACHE_TIMEOUT = 8 * 60 * 60  # 8 hours
LOCAL_VERSION = parse(authentik_version())


def _set_prom_info():
    """Set prometheus info for version"""
    PROM_INFO.info(
        {
            "version": authentik_version(),
            "latest": UpdateVersionInfo.get_cached().version,
            "build_hash": authentik_build_hash(),
        }
    )


class UpdateVersionReason(StrEnum):
    """Reason why an authentik update was released"""

    bugfix = "bugfix"
    feature = "feature"
    security = "security"
    other = "other"


class UpdateVersionInfo(BaseModel):
    version: str
    changelog: str
    changelog_url: HttpUrl
    reason: UpdateVersionReason
    valid: bool = Field(default=True)

    @staticmethod
    def get_invalid() -> UpdateVersionInfo:
        return UpdateVersionInfo(
            version="0.0.0",
            changelog="",
            changelog_url="https://docs.goauthentik.io",
            reason=UpdateVersionReason.other,
            valid=False,
        )

    @staticmethod
    def get_cached() -> UpdateVersionInfo:
        return cache.get(VERSION_CACHE_KEY, UpdateVersionInfo.get_invalid())

    @staticmethod
    def cache_invalid():
        cache.set(
            VERSION_CACHE_KEY,
            UpdateVersionInfo(
                version="0.0.0",
                changelog="",
                changelog_url="",
                reason=UpdateVersionReason.other,
                valid=False,
            ),
            VERSION_CACHE_TIMEOUT,
        )


@actor(description=_("Update latest version info."))
def update_latest_version():
    self = CurrentTask.get_task()
    if CONFIG.get_bool("disable_update_check"):
        UpdateVersionInfo.cache_invalid()
        self.info("Version check disabled.")
        return
    try:
        response = get_http_session().get(
            "https://version.goauthentik.io/versions/authentik/latest.json"
        )
        response.raise_for_status()
        data = response.json()
        upstream_version = UpdateVersionInfo.model_validate(data.get("stable", {}))
        cache.set(VERSION_CACHE_KEY, upstream_version, VERSION_CACHE_TIMEOUT)
        self.info("Successfully updated latest Version")
        _set_prom_info()
        # Check if upstream version is newer than what we're running,
        # and if no event exists yet, create one.
        if LOCAL_VERSION < parse(upstream_version.version):
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
                changelog=upstream_version.changelog_url,
            ).save()
    except (RequestException, IndexError, ValidationError) as exc:
        UpdateVersionInfo.cache_invalid()
        raise exc
