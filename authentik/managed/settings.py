"""managed Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "managed_reconcile": {
        "task": "authentik.managed.tasks.managed_reconcile",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "authentik_scheduled"},
    },
    "managed_config_file_discovery": {
        "task": "authentik.managed.tasks.config_file_discovery",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "authentik_scheduled"},
    },
}
