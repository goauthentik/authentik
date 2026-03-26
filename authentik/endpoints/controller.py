from django.db import models
from structlog.stdlib import BoundLogger, get_logger

from authentik.endpoints.models import Connector
from authentik.flows.stage import StageView
from authentik.lib.sentry import SentryIgnoredException

MERGED_VENDOR = "goauthentik.io/@merged"


class Capabilities(models.TextChoices):
    # Automatically enrolled through user action
    ENROLL_AUTOMATIC_USER = "enroll_automatic_user"
    # Automatically enrolled through connector integration
    ENROLL_AUTOMATIC_API = "enroll_automatic_api"
    # Manually enrolled with user interaction (user scanning a QR code for example)
    ENROLL_MANUAL_USER = "enroll_manual_user"
    # Supported for use with Endpoints stage
    STAGE_ENDPOINTS = "stage_endpoints"


class ConnectorSyncException(SentryIgnoredException):
    """Base exceptions for errors during sync"""


class BaseController[T: "Connector"]:

    connector: T
    logger: BoundLogger

    def __init__(self, connector: T) -> None:
        self.connector = connector
        self.logger = get_logger().bind(connector=connector.name)

    @staticmethod
    def vendor_identifier() -> str:
        raise NotImplementedError

    def capabilities(self) -> list[Capabilities]:
        return []

    def stage_view_enrollment(self) -> StageView | None:
        return None

    def stage_view_authentication(self) -> StageView | None:
        return None

    def sync_endpoints(self):
        raise NotImplementedError
