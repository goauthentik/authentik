"""Outposts Settings"""

from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "outposts_controller": {
        "task": "authentik.outposts.tasks.outpost_controller_all",
        "schedule": crontab(minute=fqdn_rand("outposts_controller"), hour="*/4"),
        "options": {"queue": "authentik_scheduled"},
    },
    "outpost_token_ensurer": {
        "task": "authentik.outposts.tasks.outpost_token_ensurer",
        "schedule": crontab(minute=fqdn_rand("outpost_token_ensurer"), hour="*/8"),
        "options": {"queue": "authentik_scheduled"},
    },
    "outpost_connection_discovery": {
        "task": "authentik.outposts.tasks.outpost_connection_discovery",
        "schedule": crontab(minute=fqdn_rand("outpost_connection_discovery"), hour="*/8"),
        "options": {"queue": "authentik_scheduled"},
    },
}
