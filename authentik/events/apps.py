"""authentik events app"""
from datetime import timedelta
from importlib import import_module

from django.apps import AppConfig
from django.db import ProgrammingError
from django.utils.timezone import now


class AuthentikEventsConfig(AppConfig):
    """authentik events app"""

    name = "authentik.events"
    label = "authentik_events"
    verbose_name = "authentik Events"

    def ready(self):
        import_module("authentik.events.signals")
        try:
            from authentik.events.models import Event

            date_from = now() - timedelta(days=1)

            for event in Event.objects.filter(created__gte=date_from):
                event._set_prom_metrics()
        except ProgrammingError:
            pass
