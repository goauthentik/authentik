"""authentik outposts app config"""
from importlib import import_module

from django.apps import AppConfig
from django.db import DatabaseError, ProgrammingError
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
MANAGED_OUTPOST = "goauthentik.io/outposts/embedded"


class AuthentikOutpostConfig(AppConfig):
    """authentik outposts app config"""

    name = "authentik.outposts"
    label = "authentik_outposts"
    verbose_name = "authentik Outpost"

    def ready(self):
        import_module("authentik.outposts.signals")
        try:
            self.reconcile_embedded_outpost()
        except (ProgrammingError, DatabaseError):
            pass

    def reconcile_embedded_outpost(self):
        """Reconcile embedded outpost"""
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
