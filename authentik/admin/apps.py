"""authentik admin app config"""
from django.apps import AppConfig


class AuthentikAdminConfig(AppConfig):
    """authentik admin app config"""

    name = "authentik.admin"
    label = "authentik_admin"
    verbose_name = "authentik Admin"

    def ready(self):
        from authentik.admin.tasks import clear_update_notifications

        clear_update_notifications.delay()
