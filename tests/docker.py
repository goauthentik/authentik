"""authentik e2e testing utilities"""

from collections.abc import Callable
from os import environ
from time import sleep
from typing import Any
from unittest.case import TestCase

from docker import DockerClient, from_env
from docker.errors import DockerException
from docker.models.containers import Container
from docker.models.networks import Network
from structlog.stdlib import get_logger

from authentik.lib.generators import generate_id
from authentik.lib.utils.reflection import class_to_path
from authentik.root.test_runner import get_docker_tag

IS_CI = "CI" in environ


class DockerTestCase(TestCase):
    """Mixin for dealing with containers"""

    max_healthcheck_attempts = 45

    __client: DockerClient
    __network: Network

    __label_id = generate_id()

    def setUp(self) -> None:
        self.__client = from_env()
        self.__network = self.docker_client.networks.create(name=f"authentik-test-{generate_id()}")

    @property
    def docker_client(self) -> DockerClient:
        return self.__client

    @property
    def docker_network(self) -> Network:
        return self.__network

    @property
    def docker_labels(self) -> dict[str, str]:
        return {"io.goauthentik.test": self.__label_id}

    def wait_for_container(self, container: Container) -> Container:
        """Check that container is health"""
        attempt = 0
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            sleep(1)
            attempt += 1
            if attempt >= self.max_healthcheck_attempts:
                self.output_container_logs(container)
                raise self.failureException("Container failed to start")

    def get_container_image(self, base: str) -> str:
        """Try to pull docker image based on git branch, fallback to main if not found."""
        image = f"{base}:gh-main"
        try:
            branch_image = f"{base}:{get_docker_tag()}"
            self.docker_client.images.pull(branch_image)
            return branch_image
        except DockerException:
            self.docker_client.images.pull(image)
        return image

    def run_container(self, **specs: Any) -> Container:
        if "network_mode" not in specs:
            specs["network"] = self.__network.name
        specs["labels"] = self.docker_labels
        specs["detach"] = True
        if hasattr(self, "live_server_url"):
            specs.setdefault("environment", {})
            specs["environment"]["AUTHENTIK_HOST"] = self.live_server_url
        container: Container = self.docker_client.containers.run(**specs)
        container.reload()
        state = container.attrs.get("State", {})
        if "Health" not in state:
            return container
        self.wait_for_container(container)
        return container

    def output_container_logs(self, container: Container | None = None) -> None:
        """Output the container logs to our STDOUT"""
        if not container:
            return
        if IS_CI:
            image = container.image
            if image:
                tags = image.tags[0] if len(image.tags) > 0 else str(image)
                print(f"::group::Container logs - {tags}")
        for log in container.logs().decode().split("\n"):
            print(log)
        if IS_CI:
            print("::endgroup::")

    def tearDown(self) -> None:
        containers: list[Container] = self.docker_client.containers.list(
            filters={"label": ",".join(f"{x}={y}" for x, y in self.docker_labels.items())}
        )
        for container in containers:
            self.output_container_logs(container)
            try:
                container.kill()
            except DockerException:
                pass
            try:
                container.remove(force=True)
            except DockerException:
                pass
        self.__network.remove()


def require_container_image(*names: str, fail_ok: bool = False) -> Callable[..., Any]:
    def wrapper(cls: type) -> type:
        client = from_env()
        logger = get_logger(class_to_path(cls))
        for image in names:
            try:
                client.images.get(image)
                logger.info("Container image available", image=image)
            except DockerException:
                logger.info("Pulling container image", image=image)
                try:
                    client.images.pull(image)
                except DockerException as exc:
                    if not fail_ok:
                        raise exc
        return cls

    return wrapper
