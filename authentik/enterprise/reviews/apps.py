from authentik.enterprise.apps import EnterpriseConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec


class ReportsConfig(EnterpriseConfig):
    name = "authentik.enterprise.reviews"
    label = "authentik_reviews"
    verbose_name = "authentik Enterprise.Reviews"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.enterprise.reviews.tasks import apply_lifecycle_rules

        return [
            ScheduleSpec(
                actor=apply_lifecycle_rules,
                crontab=f"{fqdn_rand('reviews_apply_lifecycle_rules')} 0 * * *",
            )
        ]
