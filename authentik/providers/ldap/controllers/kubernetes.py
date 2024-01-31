"""LDAP Provider Kubernetes Controller"""

from authentik.outposts.controllers.base import DeploymentPort
from authentik.outposts.controllers.kubernetes import KubernetesController
from authentik.outposts.models import KubernetesServiceConnection, Outpost


class LDAPKubernetesController(KubernetesController):
    """LDAP Provider Kubernetes Controller"""

    def __init__(self, outpost: Outpost, connection: KubernetesServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = [
            DeploymentPort(389, "ldap", "tcp", 3389),
            DeploymentPort(636, "ldaps", "tcp", 6636),
            DeploymentPort(9300, "http-metrics", "tcp", 9300),
        ]
