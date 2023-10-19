"""Enterprise additional settings"""
from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "enterprise_calculate_license": {
        "task": "authentik.enterprise.tasks.calculate_license",
        "schedule": crontab(minute=fqdn_rand("calculate_license"), hour="*/2"),
        "options": {"queue": "authentik_scheduled"},
    }
}
