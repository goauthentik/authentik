"""authentik outposts app config"""
from prometheus_client import Gauge
from structlog.stdlib import get_logger

from authentik.blueprints.apps import ManagedAppConfig

LOGGER = get_logger()

GAUGE_OUTPOSTS_CONNECTED = Gauge(
    "authentik_outposts_connected", "Currently connected outposts", ["outpost", "uid", "expected"]
)
GAUGE_OUTPOSTS_LAST_UPDATE = Gauge(
    "authentik_outposts_last_update",
    "Last update from any outpost",
    ["outpost", "uid", "version"],
)
MANAGED_OUTPOST = "goauthentik.io/outposts/embedded"


class AuthentikOutpostConfig(ManagedAppConfig):
    """authentik outposts app config"""

    name = "authentik.outposts"
    label = "authentik_outposts"
    verbose_name = "authentik Outpost"
    default = True

    def reconcile_load_outposts_signals(self):
        """Load outposts signals"""
        self.import_module("authentik.outposts.signals")

    def reconcile_embedded_outpost(self):
        """Ensure embedded outpost"""
        from authentik.outposts.models import (
            DockerServiceConnection,
            KubernetesServiceConnection,
            Outpost,
            OutpostConfig,
            OutpostType,
        )

        outpost, updated = Outpost.objects.update_or_create(
            defaults={
                "name": "authentik Embedded Outpost",
                "type": OutpostType.PROXY,
            },
            managed=MANAGED_OUTPOST,
        )
        if updated:
            if KubernetesServiceConnection.objects.exists():
                outpost.service_connection = KubernetesServiceConnection.objects.first()
            elif DockerServiceConnection.objects.exists():
                outpost.service_connection = DockerServiceConnection.objects.first()
            outpost.config = OutpostConfig(
                kubernetes_disabled_components=[
                    "deployment",
                    "secret",
                ]
            )
            outpost.save()
