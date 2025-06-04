"""authentik Unique Password policy app config"""

from authentik.enterprise.apps import EnterpriseConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.lib import ScheduleSpec


class AuthentikEnterprisePoliciesUniquePasswordConfig(EnterpriseConfig):
    name = "authentik.enterprise.policies.unique_password"
    label = "authentik_policies_unique_password"
    verbose_name = "authentik Enterprise.Policies.Unique Password"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.enterprise.policies.unique_password.tasks import (
            check_and_purge_password_history,
            trim_password_histories,
        )

        return [
            ScheduleSpec(
                actor_name=trim_password_histories.actor_name,
                crontab=f"{fqdn_rand('policies_unique_password_trim')} */12 * * *",
            ),
            ScheduleSpec(
                actor_name=check_and_purge_password_history.actor_name,
                crontab=f"{fqdn_rand('policies_unique_password_purge')} */24 * * *",
            ),
        ]
