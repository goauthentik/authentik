from authentik.blueprints.apps import ManagedAppConfig


class AuthentikTasksSchedulesConfig(ManagedAppConfig):
    name = "authentik.tasks.schedules"
    label = "authentik_tasks_schedules"
    verbose_name = "authentik Tasks Schedules"
    default = True

    def get_tenant_schedule_specs(self):
        from authentik.tasks.schedules.models import ScheduledModel

        schedules = []
        for Model in ScheduledModel.__subclasses__():
            for obj in Model.objects.all():
                for spec in obj.schedule_specs:
                    spec.rel_obj = obj
                    schedules.append(spec)
        return schedules
