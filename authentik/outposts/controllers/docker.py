"""Docker controller"""
from time import sleep
from typing import Dict, Tuple

from django.conf import settings
from docker import DockerClient
from docker.errors import DockerException, NotFound
from docker.models.containers import Container
from yaml import safe_dump

from authentik import __version__
from authentik.lib.config import CONFIG
from authentik.outposts.controllers.base import BaseController, ControllerException
from authentik.outposts.models import (
    DockerServiceConnection,
    Outpost,
    ServiceConnectionInvalid,
)


class DockerController(BaseController):
    """Docker controller"""

    client: DockerClient

    container: Container
    connection: DockerServiceConnection

    def __init__(self, outpost: Outpost, connection: DockerServiceConnection) -> None:
        super().__init__(outpost, connection)
        try:
            self.client = connection.client()
        except ServiceConnectionInvalid as exc:
            raise ControllerException from exc

    def _get_labels(self) -> Dict[str, str]:
        return {}

    def _get_env(self) -> Dict[str, str]:
        return {
            "AUTHENTIK_HOST": self.outpost.config.authentik_host,
            "AUTHENTIK_INSECURE": str(self.outpost.config.authentik_host_insecure),
            "AUTHENTIK_TOKEN": self.outpost.token.key,
        }

    def _comp_env(self, container: Container) -> bool:
        """Check if container's env is equal to what we would set. Return true if container needs
        to be rebuilt."""
        should_be = self._get_env()
        container_env = container.attrs.get("Config", {}).get("Env", {})
        for key, expected_value in should_be.items():
            if key not in container_env:
                continue
            if container_env[key] != expected_value:
                return True
        return False

    def _get_container(self) -> Tuple[Container, bool]:
        container_name = f"authentik-proxy-{self.outpost.uuid.hex}"
        try:
            return self.client.containers.get(container_name), False
        except NotFound:
            self.logger.info("Container does not exist, creating")
            image_prefix = CONFIG.y("outposts.docker_image_base")
            image_name = f"{image_prefix}-{self.outpost.type}:{__version__}"
            self.client.images.pull(image_name)
            container_args = {
                "image": image_name,
                "name": f"authentik-proxy-{self.outpost.uuid.hex}",
                "detach": True,
                "ports": {
                    f"{port.port}/{port.protocol.lower()}": port.port
                    for port in self.deployment_ports
                },
                "environment": self._get_env(),
                "labels": self._get_labels(),
            }
            if settings.TEST:
                del container_args["ports"]
                container_args["network_mode"] = "host"
            return (
                self.client.containers.create(**container_args),
                True,
            )

    def up(self):
        try:
            container, has_been_created = self._get_container()
            # Check if the container is out of date, delete it and retry
            if len(container.image.tags) > 0:
                tag: str = container.image.tags[0]
                _, _, version = tag.partition(":")
                if version != __version__:
                    self.logger.info(
                        "Container has mismatched version, re-creating...",
                        has=version,
                        should=__version__,
                    )
                    container.kill()
                    container.remove(force=True)
                    return self.up()
            # Check that container values match our values
            if self._comp_env(container):
                self.logger.info("Container has outdated config, re-creating...")
                container.kill()
                container.remove(force=True)
                return self.up()
            # Check that container is healthy
            if (
                container.status == "running"
                and container.attrs.get("State", {}).get("Health", {}).get("Status", "")
                != "healthy"
            ):
                # At this point we know the config is correct, but the container isn't healthy,
                # so we just restart it with the same config
                if has_been_created:
                    # Since we've just created the container, give it some time to start.
                    # If its still not up by then, restart it
                    self.logger.info(
                        "Container is unhealthy and new, giving it time to boot."
                    )
                    sleep(60)
                self.logger.info("Container is unhealthy, restarting...")
                container.restart()
                return None
            # Check that container is running
            if container.status != "running":
                self.logger.info("Container is not running, restarting...")
                container.start()
                return None
            return None
        except DockerException as exc:
            raise ControllerException from exc

    def down(self):
        try:
            container, _ = self._get_container()
            container.kill()
            container.remove()
        except DockerException as exc:
            raise ControllerException from exc

    def get_static_deployment(self) -> str:
        """Generate docker-compose yaml for proxy, version 3.5"""
        ports = [
            f"{port.port}:{port.port}/{port.protocol.lower()}"
            for port in self.deployment_ports
        ]
        image_prefix = CONFIG.y("outposts.docker_image_base")
        compose = {
            "version": "3.5",
            "services": {
                f"authentik_{self.outpost.type}": {
                    "image": f"{image_prefix}-{self.outpost.type}:{__version__}",
                    "ports": ports,
                    "environment": {
                        "AUTHENTIK_HOST": self.outpost.config.authentik_host,
                        "AUTHENTIK_INSECURE": str(
                            self.outpost.config.authentik_host_insecure
                        ),
                        "AUTHENTIK_TOKEN": self.outpost.token.key,
                    },
                    "labels": self._get_labels(),
                }
            },
        }
        return safe_dump(compose, default_flow_style=False)
