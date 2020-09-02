"""Docker Compose controller"""
from yaml import safe_dump

from passbook import __version__
from passbook.outposts.controllers.base import BaseController


class DockerComposeController(BaseController):
    """Docker Compose controller"""

    image_base = "beryju/passbook"

    def run(self):
        self.logger.warning("DockerComposeController does not implement run")
        raise NotImplementedError

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
