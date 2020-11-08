"""Outposts Settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "outposts_controller": {
        "task": "passbook.outposts.tasks.outpost_controller_all",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "passbook_scheduled"},
    },
    "outposts_service_connection_check": {
        "task": "passbook.outposts.tasks.outpost_service_connection_monitor",
        "schedule": crontab(minute=0, hour="*"),
        "options": {"queue": "passbook_scheduled"},
    },
}
