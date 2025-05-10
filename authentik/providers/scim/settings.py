"""SCIM task Settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "providers_scim_sync": {
        "task": "authentik.providers.scim.tasks.scim_sync_all",
        "schedule": crontab(minute=fqdn_rand("scim_sync_all"), hour="*/4"),
        "options": {"queue": "authentik_scheduled"},
    },
}
