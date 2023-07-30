"""Kerberos Provider Kubernetes Controller"""
from authentik.outposts.controllers.base import DeploymentPort
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.outposts.models import KubernetesServiceConnection, Outpost


class KerberosKubernetesController(KubernetesController):
    """Kerberos Provider Kubernetes Controller"""

    def __init__(self, outpost: Outpost, connection: KubernetesServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = [
            DeploymentPort(88, "kerberos-udp", "udp", 8888),
            DeploymentPort(88, "kerberos-tcp", "tcp", 8888),
            DeploymentPort(9300, "http-metrics", "tcp", 9300),
        ]
