"""Outposts Settings"""

from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "outposts_controller": {
        "task": "authentik.outposts.tasks.outpost_controller_all",
        "schedule": crontab(minute=fqdn_rand("outposts_controller"), hour="*/4"),
        "options": {"queue": "authentik_scheduled"},
    },
    "outposts_service_connection_check": {
        "task": "authentik.outposts.tasks.outpost_service_connection_monitor",
        "schedule": crontab(minute="3-59/15"),
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

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "authentik.outposts.authentication.OutpostTokenAuthentication"
        "authentik.api.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
}
