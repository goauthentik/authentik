"""authentik admin app config"""
from django.apps import AppConfig


class AuthentikAdminConfig(AppConfig):
    """authentik admin app config"""

    name = "authentik.admin"
    label = "authentik_admin"
    mountpoint = "administration/"
    verbose_name = "authentik Admin"
