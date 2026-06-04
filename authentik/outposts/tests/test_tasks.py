"""Outpost task tests."""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from authentik.outposts.models import DockerServiceConnection
from authentik.outposts.tasks import (
    discover_local_docker_connection,
    docker_socket_url,
    local_docker_socket_paths,
)


class TaskLogger:
    """Minimal task logger used by discovery helpers."""

    def info(self, message: str) -> None:
        """Discard task log output."""


class OutpostConnectionDiscoveryTests(TestCase):
    """Test outpost connection discovery helpers."""

    def test_local_docker_socket_paths(self):
        """Podman socket candidates are included after the Docker default."""
        self.assertEqual(
            local_docker_socket_paths("/run/user/1000"),
            [
                "/var/run/docker.sock",
                "/run/podman/podman.sock",
                "/run/user/1000/podman/podman.sock",
            ],
        )

    def test_docker_socket_url(self):
        """Docker socket paths are stored as Docker SDK URLs."""
        self.assertEqual(
            docker_socket_url("/run/podman/podman.sock"),
            "unix:///run/podman/podman.sock",
        )

    def test_discover_local_docker_connection_uses_first_readable_socket(self):
        """Create a local Docker connection for the first readable socket."""
        with TemporaryDirectory() as temp_dir:
            missing_socket = f"{temp_dir}/missing.sock"
            podman_socket = Path(temp_dir) / "podman.sock"
            podman_socket.touch()

            discover_local_docker_connection(
                TaskLogger(),
                [missing_socket, str(podman_socket)],
            )

        connection = DockerServiceConnection.objects.get(local=True)
        self.assertEqual(connection.name, "Local Docker connection")
        self.assertEqual(connection.url, f"unix://{podman_socket}")

    def test_discover_local_docker_connection_keeps_existing_connection(self):
        """Do not create a second local Docker connection."""
        DockerServiceConnection.objects.create(
            name="Existing local connection",
            local=True,
            url="unix:///var/run/docker.sock",
        )

        with TemporaryDirectory() as temp_dir:
            podman_socket = Path(temp_dir) / "podman.sock"
            podman_socket.touch()

            discover_local_docker_connection(TaskLogger(), [str(podman_socket)])

        self.assertEqual(DockerServiceConnection.objects.filter(local=True).count(), 1)
