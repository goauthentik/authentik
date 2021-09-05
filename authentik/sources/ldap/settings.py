"""LDAP Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "sources_ldap_sync": {
        "task": "authentik.sources.ldap.tasks.ldap_sync_all",
        "schedule": crontab(minute="*/60"),  # Run every hour
        "options": {"queue": "authentik_scheduled"},
    }
}
