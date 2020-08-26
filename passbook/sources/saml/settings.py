"""saml source settings"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "saml_source_cleanup": {
        "task": "passbook.sources.saml.tasks.clean_temporary_users",
        "schedule": crontab(minute="*/5"),
        'options': {'queue': 'passbook_scheduled'},
    }
}
