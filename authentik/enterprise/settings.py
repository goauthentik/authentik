"""Enterprise additional settings"""

from celery.schedules import crontab

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "enterprise_update_usage": {
        "task": "authentik.enterprise.tasks.enterprise_update_usage",
        "schedule": crontab(minute=fqdn_rand("enterprise_update_usage"), hour="*/2"),
        "options": {"queue": "authentik_scheduled"},
    }
}

TENANT_APPS = [
    "authentik.enterprise.audit",
    "authentik.enterprise.providers.google_workspace",
    "authentik.enterprise.providers.microsoft_entra",
    "authentik.enterprise.providers.rac",
    "authentik.enterprise.providers.ssf",
    "authentik.enterprise.stages.authenticator_endpoint_gdtc",
    "authentik.enterprise.stages.source",
]

MIDDLEWARE = ["authentik.enterprise.middleware.EnterpriseMiddleware"]
