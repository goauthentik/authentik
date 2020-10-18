"""Proxy Provider Docker Contoller"""
from typing import Dict
from urllib.parse import urlparse

from passbook.outposts.controllers.docker import DockerController
from passbook.outposts.models import Outpost
from passbook.providers.proxy.models import ProxyProvider


class ProxyDockerController(DockerController):
    """Proxy Provider Docker Contoller"""

    def __init__(self, outpost: Outpost):
        super().__init__(outpost)
        self.deployment_ports = {
            "http": 4180,
            "https": 4443,
        }

    def _get_labels(self) -> Dict[str, str]:
        hosts = []
        for proxy_provider in ProxyProvider.objects.filter(outpost__in=[self.outpost]):
            proxy_provider: ProxyProvider
            external_host_name = urlparse(proxy_provider.external_host)
            hosts.append(external_host_name)
        return {
            "traefik.frontend.rule": f"Host:{','.join(hosts)}",
            "traefik.port": "4180",
        }
