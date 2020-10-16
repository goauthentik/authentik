"""Base Controller"""
from typing import Dict

from structlog import get_logger

from passbook.lib.sentry import SentryIgnoredException
from passbook.outposts.models import Outpost


class ControllerException(SentryIgnoredException):
    """Exception raise when anything fails during controller run"""


class BaseController:
    """Base Outpost deployment controller"""

    deployment_ports: Dict[str, int]

    outpost: Outpost

    def __init__(self, outpost_pk: str):
        self.outpost = Outpost.objects.get(pk=outpost_pk)
        self.logger = get_logger(
            controller=self.__class__.__name__, outpost=self.outpost
        )
        self.deployment_ports = {}

    def run(self):
        """Called by scheduled task to reconcile deployment/service/etc"""
        raise NotImplementedError

    def get_static_deployment(self) -> str:
        """Return a static deployment configuration"""
        raise NotImplementedError
