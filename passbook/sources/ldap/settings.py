"""LDAP Settings"""
from celery.schedules import crontab

AUTHENTICATION_BACKENDS = [
    "passbook.sources.ldap.auth.LDAPBackend",
]

CELERY_BEAT_SCHEDULE = {
    "sources_ldap_sync": {
        "task": "passbook.sources.ldap.tasks.ldap_sync_all",
        "schedule": crontab(minute=0),  # Run every hour
        "options": {"queue": "passbook_scheduled"},
    }
}
