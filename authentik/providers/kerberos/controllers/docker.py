"""Kerberos Provider Docker Controller"""
from authentik.outposts.controllers.base import DeploymentPort
from authentik.outposts.controllers.docker import DockerController
from authentik.outposts.models import DockerServiceConnection, Outpost


class KerberosDockerController(DockerController):
    """Kerberos Provider Docker Controller"""

    def __init__(self, outpost: Outpost, connection: DockerServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = [
            DeploymentPort(88, "kerberos-udp", "udp", 8888),
            DeploymentPort(88, "kerberos-tcp", "tcp", 8888),
        ]
