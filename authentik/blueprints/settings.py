"""managed Settings"""
from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    # "blueprints_reconcile": {
    #     "task": "authentik.blueprints.tasks.managed_reconcile",
    #     "schedule": crontab(minute=fqdn_rand("managed_reconcile"), hour="*/4"),
    #     "options": {"queue": "authentik_scheduled"},
    # },
    "blueprints_config_file_discovery": {
        "task": "authentik.blueprints.tasks.config_file_discovery",
        "schedule": crontab(minute=fqdn_rand("config_file_discovery"), hour="*"),
        "options": {"queue": "authentik_scheduled"},
    },
}
