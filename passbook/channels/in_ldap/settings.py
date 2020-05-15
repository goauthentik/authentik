"""LDAP Settings"""
from celery.schedules import crontab

AUTHENTICATION_BACKENDS = [
    "passbook.channels.in_ldap.auth.LDAPBackend",
]

CELERY_BEAT_SCHEDULE = {
    "sync": {
        "task": "passbook.channels.in_ldap.tasks.sync",
        "schedule": crontab(minute=0),  # Run every hour
    }
}
