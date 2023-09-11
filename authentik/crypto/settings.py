"""Crypto task Settings"""
from celery.schedules import crontab

from authentik.lib.config import CONFIG
from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "crypto_certificate_discovery": {
        "task": "authentik.crypto.tasks.certificate_discovery",
        "schedule": crontab(minute=fqdn_rand("crypto_certificate_discovery"), hour="*"),
        "options": {"priority": CONFIG.get_int("worker.priority.scheduled")},
    },
}
