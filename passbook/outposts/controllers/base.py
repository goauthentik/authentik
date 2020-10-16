"""Base Controller"""
from typing import Dict, List

from structlog import get_logger
from structlog.testing import capture_logs

from passbook.lib.sentry import SentryIgnoredException
from passbook.outposts.models import Outpost


class ControllerException(SentryIgnoredException):
    """Exception raise when anything fails during controller run"""


class BaseController:
    """Base Outpost deployment controller"""

    deployment_ports: Dict[str, int]

    outpost: Outpost

    def __init__(self, outpost: Outpost):
        self.outpost = outpost
        self.logger = get_logger(
            controller=self.__class__.__name__, outpost=self.outpost
        )
        self.deployment_ports = {}

    def run(self):
        """Called by scheduled task to reconcile deployment/service/etc"""
        raise NotImplementedError

    def run_with_logs(self) -> List[str]:
        """Call .run() but capture all log output and return it."""
        with capture_logs() as logs:
            self.run()
        return [f"{x['controller']}: {x['event']}" for x in logs]

    def get_static_deployment(self) -> str:
        """Return a static deployment configuration"""
        raise NotImplementedError
