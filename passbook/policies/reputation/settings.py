"""Reputation Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "policies_reputation_ip_save": {
        "task": "passbook.policies.reputation.tasks.save_ip_reputation",
        "schedule": crontab(minute="*/5"),
        'options': {'queue': 'passbook_scheduled'},
    },
    "policies_reputation_user_save": {
        "task": "passbook.policies.reputation.tasks.save_user_reputation",
        "schedule": crontab(minute="*/5"),
        'options': {'queue': 'passbook_scheduled'},
    },
}
