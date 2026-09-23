"""authentik admin app config"""

from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate
from prometheus_client import Info

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.config import CONFIG
from authentik.lib.utils.time import fqdn_rand
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.tasks.schedules.common import ScheduleSpec

PROM_INFO = Info("authentik_version", "Currently running authentik version")

# Deprecation identifier for the configuration warning surfaced when no base URL is configured.
BASE_URL_UNSET_DEPRECATION = "authentik.admin.base_url_unset"


def ensure_system_settings(*args, using=DEFAULT_DB_ALIAS, **kwargs):
    """Make sure the system settings exist"""
    from authentik.admin.models import SystemSettings

    SystemSettings.objects.using(using).get_or_create(pk=True)


class AuthentikAdminConfig(ManagedAppConfig):
    """authentik admin app config"""

    name = "authentik.admin"
    label = "authentik_admin"
    verbose_name = "authentik Admin"
    default = True

    @ManagedAppConfig.reconcile
    def system_settings(self):
        """Make sure the system settings exist, especially after a migration"""
        post_migrate.connect(ensure_system_settings)
        ensure_system_settings()
        self._backfill_base_url()

    def _backfill_base_url(self):
        """Backfill base_url when it hasn't been set yet. Sources: AUTHENTIK_WEB__BASE_URL config
        value, then the embedded outpost's configured host. When neither is available, warn that
        the base URL must be set before it becomes required in a future release."""
        from django.core.exceptions import ValidationError

        from authentik.admin.models import SystemSettings
        from authentik.admin.utils import get_system_settings, normalize_base_url
        from authentik.core.apps import Setup
        from authentik.events.models import Event
        from authentik.outposts.models import Outpost

        settings = get_system_settings()
        if settings.base_url:
            return  # Already set
        base_url = normalize_base_url(CONFIG.get("web.base_url", ""))
        if not base_url:
            outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
            if outpost:
                base_url = normalize_base_url(outpost.config.authentik_host)
        if base_url:
            try:
                SystemSettings._meta.get_field("base_url").run_validators(base_url)
            except ValidationError:
                self.logger.warning("Discarding invalid base_url", base_url=base_url)
                base_url = ""
        if not base_url:  # No source available
            if Setup.get():  # Only nag instances that have finished setup
                self.logger.warning("Base URL is not configured")
                Event.log_deprecation(
                    BASE_URL_UNSET_DEPRECATION,
                    "No base URL is configured. A configured base URL will be required "
                    "in a future release. Set it in the system settings or via the "
                    "AUTHENTIK_WEB__BASE_URL environment variable.",
                )
            return
        SystemSettings.objects.filter(pk=settings.pk).update(base_url=base_url)
        self.logger.info("Backfilled base_url", base_url=base_url)

    @ManagedAppConfig.reconcile
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
    def schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.admin.tasks import update_latest_version

        return [
            ScheduleSpec(
                actor=update_latest_version,
                crontab=f"{fqdn_rand('admin_latest_version')} * * * *",
                paused=CONFIG.get_bool("disable_update_check"),
            ),
        ]
