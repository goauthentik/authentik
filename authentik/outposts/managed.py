"""Outpost managed objects"""
from authentik.managed.manager import EnsureExists, ObjectManager
from authentik.outposts.models import (
    DockerServiceConnection,
    KubernetesServiceConnection,
    Outpost,
    OutpostConfig,
    OutpostType,
)

MANAGED_OUTPOST = "goauthentik.io/outposts/embedded"


class OutpostManager(ObjectManager):
    """Outpost managed objects"""

    def reconcile(self):
        def outpost_created(outpost: Outpost):
            """When outpost is initially created, and we already have a service connection,
            auto-assign it."""
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

        return [
            EnsureExists(
                Outpost,
                MANAGED_OUTPOST,
                created_callback=outpost_created,
                name="authentik Embedded Outpost",
                type=OutpostType.PROXY,
            ),
        ]
