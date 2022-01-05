"""Reputation Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "policies_reputation_save": {
        "task": "authentik.policies.reputation.tasks.save_reputation",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "authentik_scheduled"},
    },
}
