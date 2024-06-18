"""RAC Provider Docker Controller"""

from authentik.outposts.controllers.docker import DockerController
from authentik.outposts.models import DockerServiceConnection, Outpost


class RACDockerController(DockerController):
    """RAC Provider Docker Controller"""

    def __init__(self, outpost: Outpost, connection: DockerServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = []
