"""managed Settings"""
from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "managed_reconcile": {
        "task": "authentik.managed.tasks.managed_reconcile",
        "schedule": crontab(minute=fqdn_rand("managed_reconcile"), hour="*/4"),
        "options": {"queue": "authentik_scheduled"},
    },
}
