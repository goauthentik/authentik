from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.reflection import all_subclasses
from authentik.tasks.schedules.lib import ScheduleSpec


class AuthentikTasksSchedulesConfig(ManagedAppConfig):
    name = "authentik.tasks.schedules"
    label = "authentik_tasks_schedules"
    verbose_name = "authentik Tasks Schedules"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.tasks.schedules.models import ScheduledModel

        schedules = []
        for Model in ScheduledModel.__subclasses__():
            if Model._meta.abstract:
                continue
            for obj in Model.objects.all():
                for spec in obj.schedule_specs:
                    spec.rel_obj = obj
                    schedules.append(spec)
        return schedules
