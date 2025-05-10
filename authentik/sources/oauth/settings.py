"""OAuth source settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "update_oauth_source_oidc_well_known": {
        "task": "authentik.sources.oauth.tasks.update_well_known_jwks",
        "schedule": crontab(minute=fqdn_rand("update_well_known_jwks"), hour="*/3"),
        "options": {"queue": "authentik_scheduled"},
    },
}
