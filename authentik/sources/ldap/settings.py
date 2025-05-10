"""LDAP Settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "sources_ldap_sync": {
        "task": "authentik.sources.ldap.tasks.ldap_sync_all",
        "schedule": crontab(minute=fqdn_rand("sources_ldap_sync"), hour="*/2"),
        "options": {"queue": "authentik_scheduled"},
    },
    "sources_ldap_connectivity_check": {
        "task": "authentik.sources.ldap.tasks.ldap_connectivity_check",
        "schedule": crontab(minute=fqdn_rand("sources_ldap_connectivity_check"), hour="*"),
        "options": {"queue": "authentik_scheduled"},
    },
}
