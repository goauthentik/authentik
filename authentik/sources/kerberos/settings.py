"""LDAP Settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "sources_kerberos_sync": {
        "task": "authentik.sources.kerberos.tasks.kerberos_sync_all",
        "schedule": crontab(minute=fqdn_rand("sources_kerberos_sync"), hour="*/2"),
        "options": {"queue": "authentik_scheduled"},
    },
    "sources_kerberos_connectivity_check": {
        "task": "authentik.sources.kerberos.tasks.kerberos_connectivity_check",
        "schedule": crontab(minute=fqdn_rand("sources_kerberos_connectivity_check"), hour="*"),
        "options": {"queue": "authentik_scheduled"},
    },
}
