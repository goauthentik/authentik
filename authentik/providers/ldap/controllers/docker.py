"""LDAP Provider Docker Controller"""
from authentik.outposts.controllers.base import DeploymentPort
from authentik.outposts.controllers.docker import DockerController
from authentik.outposts.models import DockerServiceConnection, Outpost


class LDAPDockerController(DockerController):
    """LDAP Provider Docker Controller"""

    def __init__(self, outpost: Outpost, connection: DockerServiceConnection):
        """Initialize the LDAPDockerController.

        Parameters:
            outpost (Outpost): The outpost where the Docker service is deployed.
            connection (DockerServiceConnection): The connection details for the Docker service.
        """
        super().__init__(outpost, connection)
        self.deployment_ports = [
            DeploymentPort(389, "ldap", "tcp", 3389),
            DeploymentPort(636, "ldaps", "tcp", 6636),
        ]
