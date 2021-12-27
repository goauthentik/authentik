"""managed Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "blueprints_reconcile": {
        "task": "authentik.blueprints.tasks.managed_reconcile",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "authentik_scheduled"},
    },
    "blueprints_config_file_discovery": {
        "task": "authentik.blueprints.tasks.config_file_discovery",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "authentik_scheduled"},
    },
}
