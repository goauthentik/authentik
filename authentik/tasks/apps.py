from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec


class AuthentikTasksConfig(ManagedAppConfig):
    name = "authentik.tasks"
    label = "authentik_tasks"
    verbose_name = "authentik Tasks"
    default = True

    @property
    def global_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.tasks.tasks import clean_worker_statuses

        return [
            ScheduleSpec(
                actor=clean_worker_statuses,
                crontab=f"{fqdn_rand('clean_worker_statuses')} {fqdn_rand('clean_worker_statuses', 24)} * * *",  # noqa: E501
            ),
        ]
