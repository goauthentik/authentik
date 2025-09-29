"""authentik admin settings"""

from celery.schedules import crontab
from django_tenants.utils import get_public_schema_name

from authentik.lib.utils.time import fqdn_rand

CELERY_BEAT_SCHEDULE = {
    "admin_latest_version": {
        "task": "authentik.admin.tasks.update_latest_version",
        "schedule": crontab(minute=fqdn_rand("admin_latest_version"), hour="*"),
        "tenant_schemas": [get_public_schema_name()],
        "options": {"queue": "authentik_scheduled"},
    }
}
