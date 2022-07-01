"""authentik outposts app config"""
from importlib import import_module

from django.apps import AppConfig
from prometheus_client import Gauge
from structlog.stdlib import get_logger

LOGGER = get_logger()

GAUGE_OUTPOSTS_CONNECTED = Gauge(
    "authentik_outposts_connected", "Currently connected outposts", ["outpost", "uid", "expected"]
)
GAUGE_OUTPOSTS_LAST_UPDATE = Gauge(
    "authentik_outposts_last_update",
    "Last update from any outpost",
    ["outpost", "uid", "version"],
)


class AuthentikOutpostConfig(AppConfig):
    """authentik outposts app config"""

    name = "authentik.outposts"
    label = "authentik_outposts"
    verbose_name = "authentik Outpost"

    def ready(self):
        import_module("authentik.outposts.signals")
        import_module("authentik.outposts.managed")
