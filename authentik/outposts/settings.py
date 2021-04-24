"""Outposts Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "outposts_controller": {
        "task": "authentik.outposts.tasks.outpost_controller_all",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "authentik_scheduled"},
    },
    "outposts_service_connection_check": {
        "task": "authentik.outposts.tasks.outpost_service_connection_monitor",
        "schedule": crontab(minute="*/60"),
        "options": {"queue": "authentik_scheduled"},
    },
    "outpost_token_ensurer": {
        "task": "authentik.outposts.tasks.outpost_token_ensurer",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "authentik_scheduled"},
    },
    "outpost_local_connection": {
        "task": "authentik.outposts.tasks.outpost_local_connection",
        "schedule": crontab(minute="*/60"),
        "options": {"queue": "authentik_scheduled"},
    },
}
