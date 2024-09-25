"""authentik admin settings"""

from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "analytics_send": {
        "task": "authentik.analytics.tasks.send_analytics",
        "schedule": crontab(
            minute=fqdn_rand("analytics_send"),
            hour=fqdn_rand("analytics_send", stop=24),
            day_of_week=fqdn_rand("analytics_send", 7),
        ),
        "options": {"queue": "authentik_scheduled"},
    }
}
