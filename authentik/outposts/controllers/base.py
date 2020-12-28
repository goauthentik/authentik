"""Base Controller"""
from dataclasses import dataclass

from structlog import get_logger
from structlog.testing import capture_logs

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

    def get_static_deployment(self) -> str:
        """Return a static deployment configuration"""
        raise NotImplementedError
