"""Base Controller"""
from dataclasses import dataclass
from os import environ
from typing import Optional

from structlog.stdlib import get_logger
from structlog.testing import capture_logs

from authentik import ENV_GIT_HASH_KEY, __version__
from authentik.lib.config import CONFIG
from authentik.lib.sentry import SentryIgnoredException
from authentik.outposts.models import Outpost, OutpostServiceConnection

FIELD_MANAGER = "goauthentik.io"


class ControllerException(SentryIgnoredException):
    """Exception raised when anything fails during controller run"""


@dataclass
class DeploymentPort:
    """Info about deployment's single port."""

    port: int
    name: str
    protocol: str
    inner_port: Optional[int] = None


class BaseController:
    """Base Outpost deployment controller"""

    deployment_ports: list[DeploymentPort]

    outpost: Outpost
    connection: OutpostServiceConnection

    def __init__(self, outpost: Outpost, connection: OutpostServiceConnection):
        self.outpost = outpost
        self.connection = connection
        self.logger = get_logger()
        self.deployment_ports = []

    # pylint: disable=invalid-name
    def up(self):
        """Called by scheduled task to reconcile deployment/service/etc"""
        raise NotImplementedError

    def up_with_logs(self) -> list[str]:
        """Call .up() but capture all log output and return it."""
        with capture_logs() as logs:
            self.up()
        return [x["event"] for x in logs]

    def down(self):
        """Handler to delete everything we've created"""
        raise NotImplementedError

    def down_with_logs(self) -> list[str]:
        """Call .down() but capture all log output and return it."""
        with capture_logs() as logs:
            self.down()
        return [x["event"] for x in logs]

    def get_static_deployment(self) -> str:
        """Return a static deployment configuration"""
        raise NotImplementedError

    def get_container_image(self) -> str:
        """Get container image to use for this outpost"""
        if self.outpost.config.container_image is not None:
            return self.outpost.config.container_image

        image_name_template: str = CONFIG.y("outposts.container_image_base")
        return image_name_template % {
            "type": self.outpost.type,
            "version": __version__,
            "build_hash": environ.get(ENV_GIT_HASH_KEY, ""),
        }
