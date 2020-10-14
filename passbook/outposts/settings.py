"""Outposts Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "outposts_controller": {
        "task": "passbook.outposts.tasks.outpost_controller",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "passbook_scheduled"},
    },
}
