"""authentik admin settings"""

# CELERY_BEAT_SCHEDULE = {
#     "admin_latest_version": {
#         "task": "authentik.admin.tasks.update_latest_version",
#         "schedule": crontab(minute=fqdn_rand("admin_latest_version"), hour="*"),
#         "options": {"queue": "authentik_scheduled"},
#     }
# }
