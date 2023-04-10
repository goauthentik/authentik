"""Docker controller"""
from time import sleep
from typing import Optional
from urllib.parse import urlparse

from django.conf import settings
from django.utils.text import slugify
from docker import DockerClient as UpstreamDockerClient
from docker.errors import DockerException, NotFound
from docker.models.containers import Container
from docker.utils.utils import kwargs_from_env
from paramiko.ssh_exception import SSHException
from structlog.stdlib import get_logger
from yaml import safe_dump

from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.controllers.base import BaseClient, BaseController, ControllerException
from authentik.outposts.docker_ssh import DockerInlineSSH, SSHManagedExternallyException
from authentik.outposts.docker_tls import DockerInlineTLS
from authentik.outposts.models import (
    DockerServiceConnection,
    Outpost,
    OutpostServiceConnectionState,
    ServiceConnectionInvalid,
)


class DockerClient(UpstreamDockerClient, BaseClient):
    """Custom docker client, which can handle TLS and SSH from a database."""

    tls: Optional[DockerInlineTLS]
    ssh: Optional[DockerInlineSSH]

    def __init__(self, connection: DockerServiceConnection):
        self.tls = None
        self.ssh = None
        self.logger = get_logger()
        if connection.local:
            # Same result as DockerClient.from_env
            super().__init__(**kwargs_from_env())
        else:
            parsed_url = urlparse(connection.url)
            tls_config = False
            if parsed_url.scheme == "ssh":
                try:
                    self.ssh = DockerInlineSSH(parsed_url.hostname, connection.tls_authentication)
                    self.ssh.write()
                except SSHManagedExternallyException as exc:
                    # SSH config is managed externally
                    self.logger.info(f"SSH Managed externally: {exc}")
            else:
                self.tls = DockerInlineTLS(
                    verification_kp=connection.tls_verification,
                    authentication_kp=connection.tls_authentication,
                )
                tls_config = self.tls.write()
            try:
                super().__init__(
                    base_url=connection.url,
                    tls=tls_config,
                )
            except SSHException as exc:
                if self.ssh:
                    self.ssh.cleanup()
                raise ServiceConnectionInvalid(exc) from exc
        # Ensure the client actually works
        self.containers.list()

    def fetch_state(self) -> OutpostServiceConnectionState:
        try:
            return OutpostServiceConnectionState(version=self.info()["ServerVersion"], healthy=True)
        except (ServiceConnectionInvalid, DockerException):
            return OutpostServiceConnectionState(version="", healthy=False)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.tls:
            self.logger.debug("Cleaning up TLS")
            self.tls.cleanup()
        if self.ssh:
            self.logger.debug("Cleaning up SSH")
            self.ssh.cleanup()


class DockerController(BaseController):
    """Docker controller"""

    client: DockerClient

    container: Container
    connection: DockerServiceConnection

    def __init__(self, outpost: Outpost, connection: DockerServiceConnection) -> None:
        super().__init__(outpost, connection)
        if outpost.managed == MANAGED_OUTPOST:
            return
        try:
            self.client = DockerClient(connection)
        except DockerException as exc:
            self.logger.warning(exc)
            raise ControllerException from exc

    @property
    def name(self) -> str:
        """Get the name of the object this reconciler manages"""
        return (
            self.outpost.config.object_naming_template
            % {
                "name": slugify(self.outpost.name),
                "uuid": self.outpost.uuid.hex,
            }
        ).lower()

    def _get_labels(self) -> dict[str, str]:
        labels = {
            "io.goauthentik.outpost-uuid": self.outpost.pk.hex,
        }
        if self.outpost.config.docker_labels:
            labels.update(self.outpost.config.docker_labels)
        return labels

    def _get_env(self) -> dict[str, str]:
        return {
            "AUTHENTIK_HOST": self.outpost.config.authentik_host.lower(),
            "AUTHENTIK_INSECURE": str(self.outpost.config.authentik_host_insecure).lower(),
            "AUTHENTIK_TOKEN": self.outpost.token.key,
            "AUTHENTIK_HOST_BROWSER": self.outpost.config.authentik_host_browser,
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

    def _comp_labels(self, container: Container) -> bool:
        """Check if container's labels is equal to what we would set. Return true if container needs
        to be rebuilt."""
        should_be = self._get_labels()
        for key, expected_value in should_be.items():
            if key not in container.labels:
                return True
            if container.labels[key] != expected_value:
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
        # If no ports are mapped (either mapping disabled, or host network)
        if not container.ports or not self.outpost.config.docker_map_ports:
            return False
        for port in self.deployment_ports:
            key = f"{port.inner_port or port.port}/{port.protocol.lower()}"
            if not container.ports.get(key, None):
                return True
            host_matching = False
            for host_port in container.ports[key]:
                host_matching = host_port.get("HostPort") == str(port.port)
            if not host_matching:
                return True
        return False

    def try_pull_image(self):
        """Try to pull the image needed for this outpost based on the CONFIG
        `outposts.container_image_base`, but fall back to known-good images"""
        image = self.get_container_image()
        try:
            self.client.images.pull(image)
        except DockerException:  # pragma: no cover
            image = f"ghcr.io/goauthentik/{self.outpost.type}:latest"
            self.client.images.pull(image)
        return image

    def _get_container(self) -> tuple[Container, bool]:
        try:
            return self.client.containers.get(self.name), False
        except NotFound:
            self.logger.info("(Re-)creating container...")
            image_name = self.try_pull_image()
            container_args = {
                "image": image_name,
                "name": self.name,
                "detach": True,
                "environment": self._get_env(),
                "labels": self._get_labels(),
                "restart_policy": {"Name": "unless-stopped"},
                "network": self.outpost.config.docker_network,
            }
            if self.outpost.config.docker_map_ports:
                container_args["ports"] = {
                    f"{port.inner_port or port.port}/{port.protocol.lower()}": str(port.port)
                    for port in self.deployment_ports
                }
            if settings.TEST:
                del container_args["ports"]
                del container_args["network"]
                container_args["network_mode"] = "host"
            return (
                self.client.containers.create(**container_args),
                True,
            )

    def _migrate_container_name(self):  # pragma: no cover
        """Migrate 2021.9 to 2021.10+"""
        old_name = f"authentik-proxy-{self.outpost.uuid.hex}"
        try:
            old_container: Container = self.client.containers.get(old_name)
            old_container.kill()
            old_container.remove()
        except NotFound:
            return

    # pylint: disable=too-many-return-statements
    def up(self, depth=1):
        if self.outpost.managed == MANAGED_OUTPOST:
            return None
        if depth >= 10:
            raise ControllerException("Giving up since we exceeded recursion limit.")
        self._migrate_container_name()
        try:
            container, has_been_created = self._get_container()
            if has_been_created:
                container.start()
                return None
            # Check if the container is out of date, delete it and retry
            if len(container.image.tags) > 0:
                should_image = self.try_pull_image()
                if should_image not in container.image.tags:  # pragma: no cover
                    self.logger.info(
                        "Container has mismatched image, re-creating...",
                        has=container.image.tags,
                        should=should_image,
                    )
                    self.down()
                    return self.up(depth + 1)
            # Check container's ports
            if self._comp_ports(container):
                self.logger.info("Container has mis-matched ports, re-creating...")
                self.down()
                return self.up(depth + 1)
            # Check that container values match our values
            if self._comp_env(container):
                self.logger.info("Container has outdated config, re-creating...")
                self.down()
                return self.up(depth + 1)
            # Check that container values match our values
            if self._comp_labels(container):
                self.logger.info("Container has outdated labels, re-creating...")
                self.down()
                return self.up(depth + 1)
            if (
                container.attrs.get("HostConfig", {})
                .get("RestartPolicy", {})
                .get("Name", "")
                .lower()
                != "unless-stopped"
            ):
                self.logger.info("Container has mis-matched restart policy, re-creating...")
                self.down()
                return self.up(depth + 1)
            # Check that container is healthy
            if container.status == "running" and container.attrs.get("State", {}).get(
                "Health", {}
            ).get("Status", "") not in ["healthy", "starting"]:
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
        if self.outpost.managed == MANAGED_OUTPOST:
            return
        try:
            container, _ = self._get_container()
            if container.status == "running":
                self.logger.info("Stopping container.")
                container.kill()
            self.logger.info("Removing container.")
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
                        "AUTHENTIK_HOST_BROWSER": self.outpost.config.authentik_host_browser,
                    },
                    "labels": self._get_labels(),
                }
            },
        }
        return safe_dump(compose, default_flow_style=False)
