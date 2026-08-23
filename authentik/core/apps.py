"""authentik core app config"""

import os

from django.utils.translation import gettext_lazy as _

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.config import CONFIG
from authentik.lib.tracing import OTEL_DEFER_PROVIDER_ENV_VAR, otel_init, otel_instrument
from authentik.tasks.schedules.common import ScheduleSpec
from authentik.tenants.flags import Flag


class Setup(Flag[bool], key="setup"):

    default = False
    visibility = "system"


class AppAccessWithoutBindings(Flag[bool], key="core_default_app_access"):

    default = True
    visibility = "none"
    description = _("Applications with no policies bound can be accessed by any user.")


class AuthentikCoreConfig(ManagedAppConfig):
    """authentik core app config"""

    name = "authentik.core"
    label = "authentik_core"
    verbose_name = "authentik Core"
    mountpoint = ""
    default = True

    def ready(self) -> None:
        if CONFIG.get_bool("error_reporting.enabled", False):
            # Under gunicorn's preload_app, the real TracerProvider must be created after
            # the fork instead (see lifecycle/gunicorn.conf.py's post_fork hook)
            if os.environ.get(OTEL_DEFER_PROVIDER_ENV_VAR):
                otel_instrument()
            else:
                otel_init()
        return super().ready()

    def import_related(self):
        super().import_related()
        self.import_module("authentik.core.setup.signals")

    @ManagedAppConfig.reconcile_tenant
    def source_inbuilt(self):
        """Reconcile inbuilt source"""
        from authentik.core.models import Source

        Source.objects.update_or_create(
            defaults={
                "name": "authentik Built-in",
                "slug": "authentik-built-in",
            },
            managed=Source.MANAGED_INBUILT,
        )

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.core.tasks import clean_expired_models, clean_temporary_users

        return [
            ScheduleSpec(
                actor=clean_expired_models,
                crontab="2-59/5 * * * *",
            ),
            ScheduleSpec(
                actor=clean_temporary_users,
                crontab="9-59/5 * * * *",
            ),
        ]
