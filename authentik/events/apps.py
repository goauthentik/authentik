"""authentik events app"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikEventsConfig(AppConfig):
    """authentik events app"""

    name = "authentik.events"
    label = "authentik_events"
    verbose_name = "authentik Events"

    def ready(self):
        import_module("authentik.events.signals")
