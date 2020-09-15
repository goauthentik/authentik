"""Outposts Settings"""
from celery.schedules import crontab

# CELERY_BEAT_SCHEDULE = {
#     "outposts_k8s": {
#         "task": "passbook.outposts.tasks.outpost_k8s_controller",
#         "schedule": crontab(minute="*/5"),  # Run every 5 minutes
#         "options": {"queue": "passbook_scheduled"},
#     }
# }
