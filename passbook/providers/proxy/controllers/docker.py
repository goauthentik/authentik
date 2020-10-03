"""Proxy Provider Docker Contoller"""
from passbook.outposts.controllers.docker import DockerController


class ProxyDockerController(DockerController):
    """Proxy Provider Docker Contoller"""

    def __init__(self, outpost_pk: str):
        super().__init__(outpost_pk)
        self.deployment_ports = {
            "http": 4180,
            "https": 4443,
        }
