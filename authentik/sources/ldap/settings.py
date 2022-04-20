"""LDAP Settings"""
from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "sources_ldap_sync": {
        "task": "authentik.sources.ldap.tasks.ldap_sync_all",
        "schedule": crontab(minute=fqdn_rand("sources_ldap_sync"), hour="*/2"),
        "options": {"queue": "authentik_scheduled"},
    }
}
