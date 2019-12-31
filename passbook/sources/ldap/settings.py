"""LDAP Settings"""
from celery.schedules import crontab

AUTHENTICATION_BACKENDS = [
    "passbook.sources.ldap.auth.LDAPBackend",
]

CELERY_BEAT_SCHEDULE = {
    "sync": {
        "task": "passbook.sources.ldap.tasks.sync",
        "schedule": crontab(minute=0),  # Run every hour
    }
}
