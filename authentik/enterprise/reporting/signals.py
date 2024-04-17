from json import dumps

from celery.schedules import crontab
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from authentik.enterprise.reporting.models import Report


@receiver(post_save, sender=Report)
def report_post_save(sender, instance: Report, **_):
    schedule = CrontabSchedule.from_schedule(crontab())
    schedule.save()
    PeriodicTask.objects.update_or_create(
        name=str(instance.pk),
        defaults={
            "crontab": schedule,
            "task": "authentik.enterprise.reporting.tasks.process_report",
            "queue": "authentik_reporting",
            "description": f"Report {instance.name}",
            "kwargs": dumps(
                {
                    "report_uuid": str(instance.pk),
                }
            ),
        },
    )


@receiver(pre_delete, sender=Report)
def report_pre_delete(sender, instance: Report, **_):
    PeriodicTask.objects.filter(name=str(instance.pk)).delete()
    # Cleanup schedules without any tasks
    CrontabSchedule.objects.filter(periodictask__isnull=True).delete()
