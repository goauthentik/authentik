"""Stage authenticator webauthn Settings"""

from celery.schedules import crontab

from authentik.common.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "stages_authenticator_webauthn_import_mds": {
        "task": "authentik.stages.authenticator_webauthn.tasks.webauthn_mds_import",
        "schedule": crontab(
            minute=fqdn_rand("webauthn_mds_import"),
            hour=fqdn_rand("webauthn_mds_import", 24),
            day_of_week=fqdn_rand("webauthn_mds_import", 7),
        ),
        "options": {"queue": "authentik_scheduled"},
    },
}
