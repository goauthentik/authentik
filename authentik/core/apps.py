"""authentik core app config"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikCoreConfig(AppConfig):
    """authentik core app config"""

    name = "authentik.core"
    label = "authentik_core"
    verbose_name = "authentik Core"
    mountpoint = ""

    def ready(self):
        import_module("authentik.core.signals")
        import_module("authentik.core.managed")
