"""Docker testing helpers"""

import os
from time import sleep
from typing import TYPE_CHECKING, Any
from unittest.case import TestCase

from docker import DockerClient, from_env
from docker.errors import DockerException
from docker.models.containers import Container
from docker.models.networks import Network

from authentik.lib.generators import generate_id
from tests import IS_CI

if TYPE_CHECKING:
    from authentik.outposts.models import Outpost


def get_docker_tag() -> str:
    """Get docker-tag based off of CI variables"""
    env_pr_branch = "GITHUB_HEAD_REF"
    default_branch = "GITHUB_REF"
    branch_name = os.environ.get(default_branch, "main")
    if os.environ.get(env_pr_branch, "") != "":
        branch_name = os.environ[env_pr_branch]
    branch_name = branch_name.replace("refs/heads/", "").replace("/", "-")
    return f"gh-{branch_name}"


class DockerTestCase(TestCase):
    """Mixin for dealing with containers"""

    max_healthcheck_attempts = 30

    __client: DockerClient
    __network: Network

    __label_id = generate_id()

    def setUp(self) -> None:
        self.__client = from_env()
        self.__network = self.docker_client.networks.create(
            name=f"authentik-test-{self.__label_id}"
        )
        super().setUp()

    @property
    def docker_client(self) -> DockerClient:
        return self.__client

    @property
    def docker_network(self) -> Network:
        return self.__network

    @property
    def docker_labels(self) -> dict:
        return {"io.goauthentik.test": self.__label_id}

    def get_container_image(self, base: str) -> str:
        """Try to pull docker image based on git branch, fallback to main if not found."""
        image = f"{base}:gh-main"
        if not IS_CI:
            return image
        try:
            branch_image = f"{base}:{get_docker_tag()}"
            self.docker_client.images.pull(branch_image)
            return branch_image
        except DockerException:
            self.docker_client.images.pull(image)
        return image

    def run_container(self, **specs: dict[str, Any]) -> Container:
        if "network_mode" not in specs:
            specs["network"] = self.__network.name
        specs["labels"] = self.docker_labels
        specs["detach"] = True
        if hasattr(self, "live_server_url"):
            specs.setdefault("environment", {})
            specs["environment"]["AUTHENTIK_HOST"] = self.live_server_url
        container = self.docker_client.containers.run(**specs)
        container.reload()
        state = container.attrs.get("State", {})
        if "Health" not in state:
            return container
        self.wait_for_container(container)
        return container

    def output_container_logs(self, container: Container | None = None):
        """Output the container logs to our STDOUT"""
        if IS_CI:
            image = container.image
            tags = image.tags[0] if len(image.tags) > 0 else str(image)
            print(f"::group::Container logs - {tags}")
        for log in container.logs().decode().split("\n"):
            print(log)
        if IS_CI:
            print("::endgroup::")

    def tearDown(self):
        containers: list[Container] = self.docker_client.containers.list(
            filters={"label": ",".join(f"{x}={y}" for x, y in self.docker_labels.items())}
        )
        for container in containers:
            self.output_container_logs(container)
            try:
                container.stop()
            except DockerException:
                pass
            try:
                container.remove(force=True)
            except DockerException:
                pass
        self.__network.remove()
        super().tearDown()

    def wait_for_container(self, container: Container):
        """Check that container is health"""
        attempt = 0
        while attempt < self.max_healthcheck_attempts:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            attempt += 1
            sleep(0.5)
        self.failureException("Container failed to start")

    def wait_for_outpost(self, outpost: "Outpost"):
        # Wait until outpost healthcheck succeeds
        attempt = 0
        while attempt < self.max_healthcheck_attempts:
            if len(outpost.state) > 0:
                state = outpost.state[0]
                if state.last_seen:
                    return
            attempt += 1
            sleep(0.5)
        self.failureException("Outpost failed to become healthy")
