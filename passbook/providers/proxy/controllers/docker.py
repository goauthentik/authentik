"""Proxy Provider Docker Contoller"""
from passbook.outposts.controllers.docker import DockerController
from passbook.outposts.models import Outpost


class ProxyDockerController(DockerController):
    """Proxy Provider Docker Contoller"""

    def __init__(self, outpost: Outpost):
        super().__init__(outpost)
        self.deployment_ports = {
            "http": 4180,
            "https": 4443,
        }
