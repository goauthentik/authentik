"""Base Controller"""
from dataclasses import dataclass
from typing import Optional

from structlog.stdlib import get_logger
from structlog.testing import capture_logs

from authentik import __version__, get_build_hash
from authentik.lib.config import CONFIG
from authentik.lib.sentry import SentryIgnoredException
from authentik.outposts.models import (
    Outpost,
    OutpostServiceConnection,
    OutpostServiceConnectionState,
)

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


class BaseClient:
    """Base class for custom clients"""

    def fetch_state(self) -> OutpostServiceConnectionState:
        """Get state, version info"""
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Cleanup after usage"""


class BaseController:
    """Base Outpost deployment controller"""

    deployment_ports: list[DeploymentPort]
    client: BaseClient
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Cleanup after usage"""
        if hasattr(self, "client"):
            self.client.__exit__(exc_type, exc_value, traceback)

    def get_static_deployment(self) -> str:
        """Return a static deployment configuration"""
        raise NotImplementedError

    def get_container_image(self) -> str:
        """Get container image to use for this outpost"""
        if self.outpost.config.container_image is not None:
            return self.outpost.config.container_image

        image_name_template: str = CONFIG.get("outposts.container_image_base")
        return image_name_template % {
            "type": self.outpost.type,
            "version": __version__,
            "build_hash": get_build_hash(),
        }
