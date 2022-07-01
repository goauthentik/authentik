"""authentik events app"""
from importlib import import_module

from django.apps import AppConfig
from prometheus_client import Gauge

GAUGE_TASKS = Gauge(
    "authentik_system_tasks",
    "System tasks and their status",
    ["task_name", "task_uid", "status"],
)


class AuthentikEventsConfig(AppConfig):
    """authentik events app"""

    name = "authentik.events"
    label = "authentik_events"
    verbose_name = "authentik Events"

    def ready(self):
        import_module("authentik.events.signals")
