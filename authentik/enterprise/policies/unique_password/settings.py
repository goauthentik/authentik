"""Unique Password Policy settings"""

from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "policies_unique_password_trim_history": {
        "task": "authentik.enterprise.policies.unique_password.tasks.trim_all_password_histories",
        "schedule": crontab(minute=fqdn_rand("policies_unique_password_trim"), hour="*/12"),
        "options": {"queue": "authentik_scheduled"},
    },
    "policies_unique_password_check_purge": {
        "task": (
            "authentik.enterprise.policies.unique_password.tasks.check_and_purge_password_history"
        ),
        "schedule": crontab(minute=fqdn_rand("policies_unique_password_purge"), hour="*/24"),
        "options": {"queue": "authentik_scheduled"},
    },
}
