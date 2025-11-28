from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.reflection import get_apps
from authentik.tasks.schedules.common import ScheduleSpec


class AuthentikTasksSchedulesConfig(ManagedAppConfig):
    name = "authentik.tasks.schedules"
    label = "authentik_tasks_schedules"
    verbose_name = "authentik Tasks Schedules"
    default = True

    @property
    def tenant_schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.tasks.schedules.models import ScheduledModel

        schedules = []
        for Model in ScheduledModel.models():
            for obj in Model.objects.all():
                for spec in obj.schedule_specs:
                    spec.rel_obj = obj
                    spec.identifier = obj.pk
                    schedules.append(spec)
        return schedules

    def _reconcile_schedules(self, specs: list[ScheduleSpec]):
        from django.db import transaction

        from authentik.tasks.schedules.models import Schedule

        schedules_to_send = []
        with transaction.atomic():
            pks_to_keep = []
            for spec in specs:
                schedule = spec.update_or_create()
                pks_to_keep.append(schedule.pk)
                if spec.send_on_startup:
                    schedules_to_send.append(schedule)
            Schedule.objects.exclude(pk__in=pks_to_keep).delete()
        for schedule in schedules_to_send:
            schedule.send()

    @ManagedAppConfig.reconcile_tenant
    def reconcile_tenant_schedules(self):
        from authentik.tenants.utils import get_current_tenant, get_public_schema_name

        schedule_specs = []
        for app in get_apps():
            schedule_specs.extend(app.tenant_schedule_specs)
            if get_current_tenant().schema_name == get_public_schema_name():
                schedule_specs.extend(app.global_schedule_specs)
        self._reconcile_schedules(schedule_specs)
