"""authentik core app config"""
from django.apps import AppConfig


class AuthentikCoreConfig(AppConfig):
    """authentik core app config"""

    name = "authentik.core"
    label = "authentik_core"
    verbose_name = "authentik Core"
    mountpoint = ""
