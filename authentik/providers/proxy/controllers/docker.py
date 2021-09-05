"""Proxy Provider Docker Contoller"""
from urllib.parse import urlparse

from authentik.outposts.controllers.base import DeploymentPort
from authentik.outposts.controllers.docker import DockerController
from authentik.outposts.models import DockerServiceConnection, Outpost
from authentik.providers.proxy.models import ProxyProvider


class ProxyDockerController(DockerController):
    """Proxy Provider Docker Contoller"""

    def __init__(self, outpost: Outpost, connection: DockerServiceConnection):
        super().__init__(outpost, connection)
        self.deployment_ports = [
            DeploymentPort(4180, "http", "tcp"),
            DeploymentPort(4443, "https", "tcp"),
        ]

    def _get_labels(self) -> dict[str, str]:
        hosts = []
        for proxy_provider in ProxyProvider.objects.filter(outpost__in=[self.outpost]):
            proxy_provider: ProxyProvider
            external_host_name = urlparse(proxy_provider.external_host)
            hosts.append(f"`{external_host_name.netloc}`")
        traefik_name = f"ak-outpost-{self.outpost.pk.hex}"
        labels = super()._get_labels()
        labels["traefik.enable"] = "true"
        labels[f"traefik.http.routers.{traefik_name}-router.rule"] = f"Host({','.join(hosts)})"
        labels[f"traefik.http.routers.{traefik_name}-router.tls"] = "true"
        labels[f"traefik.http.routers.{traefik_name}-router.service"] = f"{traefik_name}-service"
        labels[f"traefik.http.services.{traefik_name}-service.loadbalancer.healthcheck.path"] = "/"
        labels[f"traefik.http.services.{traefik_name}-service.loadbalancer.server.port"] = "4180"
        return labels
