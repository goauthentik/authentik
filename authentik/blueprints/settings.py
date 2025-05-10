"""blueprint Settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "blueprints_v1_discover": {
        "task": "authentik.blueprints.v1.tasks.blueprints_discovery",
        "schedule": crontab(minute=fqdn_rand("blueprints_v1_discover"), hour="*"),
        "options": {"queue": "authentik_scheduled"},
    },
    "blueprints_v1_cleanup": {
        "task": "authentik.blueprints.v1.tasks.clear_failed_blueprints",
        "schedule": crontab(minute=fqdn_rand("blueprints_v1_cleanup"), hour="*"),
        "options": {"queue": "authentik_scheduled"},
    },
}
