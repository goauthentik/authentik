"""authentik core app config"""

from authentik.blueprints.apps import ManagedAppConfig
from authentik.tasks.schedules.common import ScheduleSpec


class AuthentikCoreConfig(ManagedAppConfig):
    """authentik core app config"""

    name = "authentik.core"
    label = "authentik_core"
    verbose_name = "authentik Core"
    mountpoint = ""
    default = True

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
