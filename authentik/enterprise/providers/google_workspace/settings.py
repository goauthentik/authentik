"""Google workspace provider task Settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "providers_google_workspace_sync": {
        "task": "authentik.enterprise.providers.google_workspace.tasks.google_workspace_sync_all",
        "schedule": crontab(minute=fqdn_rand("google_workspace_sync_all"), hour="*/4"),
        "options": {"queue": "authentik_scheduled"},
    },
}
