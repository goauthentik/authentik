"""Reputation Settings"""
from celery.schedules import crontab

from authentik.lib.config import CONFIG

CELERY_BEAT_SCHEDULE = {
    "policies_reputation_save": {
        "task": "authentik.policies.reputation.tasks.save_reputation",
        "schedule": crontab(minute="1-59/5"),
        "options": {"priority": CONFIG.get_int("worker.priority.scheduled")},
    },
}
