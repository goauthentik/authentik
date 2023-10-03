"""Radius Provider Docker Controller"""
from authentik.outposts.controllers.base import DeploymentPort
from authentik.outposts.controllers.docker import DockerController
from authentik.outposts.models import DockerServiceConnection, Outpost


class RadiusDockerController(DockerController):
    """Radius Provider Docker Controller"""

    def __init__(self, outpost: Outpost, connection: DockerServiceConnection):
        """
        Initializes a new instance of the RadiusDockerController class.

        Parameters:
            outpost (Outpost): The outpost associated with the controller.
            connection (DockerServiceConnection): The connection associated with the controller.
        """
        super().__init__(outpost, connection)
        self.deployment_ports = [
            DeploymentPort(1812, "radius", "udp", 1812),
        ]
