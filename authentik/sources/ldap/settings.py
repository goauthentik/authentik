"""LDAP Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "sources_ldap_sync": {
        "task": "authentik.sources.ldap.tasks.ldap_sync_all",
        "schedule": crontab(minute="*/120"),  # Run every other hour
        "options": {"queue": "authentik_scheduled"},
    }
}
