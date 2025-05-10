"""Microsoft Entra provider task Settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "providers_microsoft_entra_sync": {
        "task": "authentik.enterprise.providers.microsoft_entra.tasks.microsoft_entra_sync_all",
        "schedule": crontab(minute=fqdn_rand("microsoft_entra_sync_all"), hour="*/4"),
        "options": {"queue": "authentik_scheduled"},
    },
}
