"""Crypto task Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "crypto_certificate_discovery": {
        "task": "authentik.crypto.tasks.certificate_discovery",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "authentik_scheduled"},
    },
}
