"""Plex source settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "check_plex_token": {
        "task": "authentik.sources.plex.tasks.check_plex_token_all",
        "schedule": crontab(minute="31", hour="*/3"),
        "options": {"queue": "authentik_scheduled"},
    },
}
