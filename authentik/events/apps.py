"""authentik events app"""
from prometheus_client import Gauge

from authentik.blueprints.apps import ManagedAppConfig

GAUGE_TASKS = Gauge(
    "authentik_system_tasks",
    "System tasks and their status",
    ["task_name", "task_uid", "status"],
)


class AuthentikEventsConfig(ManagedAppConfig):
    """authentik events app"""

    name = "authentik.events"
    label = "authentik_events"
    verbose_name = "authentik Events"
    default = True

    def reconcile_load_events_signals(self):
        """Load events signals"""
        self.import_module("authentik.events.signals")
