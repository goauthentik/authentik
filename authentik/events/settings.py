"""Event Settings"""
from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "events_notification_cleanup": {
        "task": "authentik.events.tasks.notification_cleanup",
        "schedule": crontab(minute=fqdn_rand("notification_cleanup"), hour="*/8"),
        "options": {"queue": "authentik_scheduled"},
    },
}
