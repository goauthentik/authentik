"""Docker controller"""
from docker import DockerClient, from_env
from docker.errors import NotFound
from docker.models.containers import Container
from yaml import safe_dump

from passbook import __version__
from passbook.outposts.controllers.base import BaseController


class DockerController(BaseController):
    """Docker controller"""

    client: DockerClient

    container: Container

    image_base = "beryju/passbook"

    def __init__(self, outpost_pk: str) -> None:
        super().__init__(outpost_pk)
        self.client = from_env()

    def _get_container(self) -> Container:
        container_name = f"passbook-proxy-{self.outpost.uuid.hex}"
        try:
            return self.client.containers.get(container_name)
        except NotFound:
            return self.client.containers.create(
                image=f"{self.image_base}-{self.outpost.type}:{__version__}",
                name=f"passbook-proxy-{self.outpost.uuid.hex}",
                detach=True,
                ports={x: x for _, x in self.deployment_ports.items()},
                environment={
                    "PASSBOOK_HOST": self.outpost.config.passbook_host,
                    "PASSBOOK_INSECURE": str(
                        self.outpost.config.passbook_host_insecure
                    ),
                    "PASSBOOK_TOKEN": self.outpost.token.token_uuid.hex,
                },
            )

    def run(self):
        container = self._get_container()
        # Check if the container is out of date, delete it and retry
        if len(container.image.tags) > 0:
            tag: str = container.iamge.tags[0]
            _, _, version = tag.partition(":")
            if version != __version__:
                container.kill()
                container.remove(force=True)
                return self.run()
        if container.status != "running":
            container.start()
        return None

    def get_static_deployment(self) -> str:
        """Generate docker-compose yaml for proxy, version 3.5"""
        ports = [f"{x}:{x}" for _, x in self.deployment_ports.items()]
        compose = {
            "version": "3.5",
            "services": {
                f"passbook_{self.outpost.type}": {
                    "image": f"{self.image_base}-{self.outpost.type}:{__version__}",
                    "ports": ports,
                    "environment": {
                        "PASSBOOK_HOST": self.outpost.config.passbook_host,
                        "PASSBOOK_INSECURE": str(
                            self.outpost.config.passbook_host_insecure
                        ),
                        "PASSBOOK_TOKEN": self.outpost.token.token_uuid.hex,
                    },
                }
            },
        }
        return safe_dump(compose, default_flow_style=False)
