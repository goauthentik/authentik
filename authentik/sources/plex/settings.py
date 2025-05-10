"""Plex source settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "check_plex_token": {
        "task": "authentik.sources.plex.tasks.check_plex_token_all",
        "schedule": crontab(minute=fqdn_rand("check_plex_token"), hour="*/3"),
        "options": {"queue": "authentik_scheduled"},
    },
}
