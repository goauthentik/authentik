"""Radius Provider Kubernetes Controller"""

from authentik.outposts.controllers.base import DeploymentPort
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.outposts.models import KubernetesServiceConnection, Outpost


class RadiusKubernetesController(KubernetesController):
    """Radius Provider Kubernetes Controller"""

    def __init__(self, outpost: Outpost, connection: KubernetesServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = [
            DeploymentPort(1812, "radius", "udp", 1812),
        ]
