"""Docker controller"""
from time import sleep

from django.conf import settings
from docker import DockerClient
from docker.errors import DockerException, NotFound
from docker.models.containers import Container
from yaml import safe_dump

from authentik import __version__
from authentik.outposts.controllers.base import BaseController, ControllerException
from authentik.outposts.models import DockerServiceConnection, Outpost, ServiceConnectionInvalid


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

    def _get_labels(self) -> dict[str, str]:
        return {}

    def _get_env(self) -> dict[str, str]:
        return {
            "AUTHENTIK_HOST": self.outpost.config.authentik_host.lower(),
            "AUTHENTIK_INSECURE": str(self.outpost.config.authentik_host_insecure).lower(),
            "AUTHENTIK_TOKEN": self.outpost.token.key,
        }

    def _comp_env(self, container: Container) -> bool:
        """Check if container's env is equal to what we would set. Return true if container needs
        to be rebuilt."""
        should_be = self._get_env()
        container_env = container.attrs.get("Config", {}).get("Env", [])
        for key, expected_value in should_be.items():
            entry = f"{key.upper()}={expected_value}"
            if entry not in container_env:
                return True
        return False

    def _comp_ports(self, container: Container) -> bool:
        """Check that the container has the correct ports exposed. Return true if container needs
        to be rebuilt."""
        # with TEST enabled, we use host-network
        if settings.TEST:
            return False
        # When the container isn't running, the API doesn't report any port mappings
        if container.status != "running":
            return False
        # {'3389/tcp': [
        #   {'HostIp': '0.0.0.0', 'HostPort': '389'},
        #   {'HostIp': '::', 'HostPort': '389'}
        # ]}
        for port in self.deployment_ports:
            key = f"{port.inner_port or port.port}/{port.protocol.lower()}"
            if key not in container.ports:
                return True
            host_matching = False
            for host_port in container.ports[key]:
                host_matching = host_port.get("HostPort") == str(port.port)
            if not host_matching:
                return True
        return False

    def _get_container(self) -> tuple[Container, bool]:
        container_name = f"authentik-proxy-{self.outpost.uuid.hex}"
        try:
            return self.client.containers.get(container_name), False
        except NotFound:
            self.logger.info("(Re-)creating container...")
            image_name = self.get_container_image()
            self.client.images.pull(image_name)
            container_args = {
                "image": image_name,
                "name": container_name,
                "detach": True,
                "ports": {
                    f"{port.inner_port or port.port}/{port.protocol.lower()}": port.port
                    for port in self.deployment_ports
                },
                "environment": self._get_env(),
                "labels": self._get_labels(),
                "restart_policy": {"Name": "unless-stopped"},
            }
            if settings.TEST:
                del container_args["ports"]
                container_args["network_mode"] = "host"
            return (
                self.client.containers.create(**container_args),
                True,
            )

    # pylint: disable=too-many-return-statements
    def up(self):
        try:
            container, has_been_created = self._get_container()
            if has_been_created:
                container.start()
                return None
            # Check if the container is out of date, delete it and retry
            if len(container.image.tags) > 0:
                tag: str = container.image.tags[0]
                if tag != self.get_container_image():
                    self.logger.info(
                        "Container has mismatched image, re-creating...",
                        has=tag,
                        should=self.get_container_image(),
                    )
                    self.down()
                    return self.up()
            # Check container's ports
            if self._comp_ports(container):
                self.logger.info("Container has mis-matched ports, re-creating...")
                self.down()
                return self.up()
            # Check that container values match our values
            if self._comp_env(container):
                self.logger.info("Container has outdated config, re-creating...")
                self.down()
                return self.up()
            if (
                container.attrs.get("HostConfig", {})
                .get("RestartPolicy", {})
                .get("Name", "")
                .lower()
                != "unless-stopped"
            ):
                self.logger.info("Container has mis-matched restart policy, re-creating...")
                self.down()
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
                    self.logger.info("Container is unhealthy and new, giving it time to boot.")
                    sleep(60)
                self.logger.info("Container is unhealthy, restarting...")
                container.restart()
                return None
            # Check that container is running
            if container.status != "running":
                self.logger.info("Container is not running, restarting...")
                container.start()
                return None
            self.logger.info("Container is running")
            return None
        except DockerException as exc:
            raise ControllerException(str(exc)) from exc

    def down(self):
        try:
            container, _ = self._get_container()
            if container.status == "running":
                container.kill()
            container.remove(force=True)
        except DockerException as exc:
            raise ControllerException(str(exc)) from exc

    def get_static_deployment(self) -> str:
        """Generate docker-compose yaml for proxy, version 3.5"""
        ports = [
            f"{port.port}:{port.inner_port or port.port}/{port.protocol.lower()}"
            for port in self.deployment_ports
        ]
        image_name = self.get_container_image()
        compose = {
            "version": "3.5",
            "services": {
                f"authentik_{self.outpost.type}": {
                    "image": image_name,
                    "ports": ports,
                    "environment": {
                        "AUTHENTIK_HOST": self.outpost.config.authentik_host,
                        "AUTHENTIK_INSECURE": str(self.outpost.config.authentik_host_insecure),
                        "AUTHENTIK_TOKEN": self.outpost.token.key,
                    },
                    "labels": self._get_labels(),
                }
            },
        }
        return safe_dump(compose, default_flow_style=False)
