"""authentik admin settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "admin_latest_version": {
        "task": "authentik.admin.tasks.update_latest_version",
        "schedule": crontab(minute=0),  # Run every hour
        "options": {"queue": "authentik_scheduled"},
    }
}
