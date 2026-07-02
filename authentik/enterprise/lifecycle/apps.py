from authentik.enterprise.apps import EnterpriseConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec


class ReportsConfig(EnterpriseConfig):
    name = "authentik.enterprise.lifecycle"
    label = "authentik_lifecycle"
    verbose_name = "authentik Enterprise.Lifecycle"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.enterprise.lifecycle.tasks import (
            apply_lifecycle_rules,
            execute_due_offboardings,
        )

        return [
            ScheduleSpec(
                actor=apply_lifecycle_rules,
                crontab=f"{fqdn_rand('lifecycle_apply_lifecycle_rules')} "
                f"{fqdn_rand('lifecycle_apply_lifecycle_rules', 24)} * * *",
            ),
            ScheduleSpec(
                actor=execute_due_offboardings,
                crontab=f"{fqdn_rand('lifecycle_execute_due_offboardings', 5)}-59/5 * * * *",
            ),
        ]
