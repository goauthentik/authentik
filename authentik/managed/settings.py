"""managed Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "managed_reconcile": {
        "task": "authentik.managed.tasks.managed_reconcile",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "authentik_scheduled"},
    },
}
