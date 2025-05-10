"""authentik admin settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "admin_latest_version": {
        "task": "authentik.admin.tasks.update_latest_version",
        "schedule": crontab(minute=fqdn_rand("admin_latest_version"), hour="*"),
        "options": {"queue": "authentik_scheduled"},
    }
}
