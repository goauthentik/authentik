from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.reflection import get_apps
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

    def _reconcile_schedules(self, specs: list[ScheduleSpec]):
        from django.db import transaction

        from authentik.tasks.schedules.models import Schedule

        with transaction.atomic():
            pks_to_keep = []
            for spec in specs:
                schedule = spec.update_or_create()
                pks_to_keep.append(schedule.pk)
            Schedule.objects.exclude(pk__in=pks_to_keep).delete()

    @ManagedAppConfig.reconcile_tenant
    def reconcile_tenant_schedules(self):
        from authentik.tenants.utils import get_current_tenant, get_public_schema_name

        schedule_specs = []
        for app in get_apps():
            schedule_specs.extend(app.tenant_schedule_specs)
            if get_current_tenant().schema_name == get_public_schema_name():
                schedule_specs.extend(app.global_schedule_specs)
        self._reconcile_schedules(schedule_specs)
