from django.db.models.signals import post_save
from django.dispatch import receiver

from authentik.tasks.schedules.models import ScheduledModel


@receiver(post_save)
def post_save_schedule_mixin(sender, instance: ScheduledModel, **_):
    if not isinstance(instance, ScheduledModel):
        return
    for spec in instance.schedule_specs:
        spec.rel_obj = instance
        schedule = spec.update_or_create()
        if spec.send_on_save:
            schedule.send()
