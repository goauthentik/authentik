from authentik.blueprints import models
from authentik.endpoints.models import Connector
from authentik.flows.stage import StageView
from authentik.lib.sentry import SentryIgnoredException


class EnrollmentMethods(models.TextChoices):
    # Automatically enrolled through user action
    AUTOMATIC_USER = "automatic_user"
    # Automatically enrolled through connector integration
    AUTOMATIC_API = "automatic_api"
    # Manually enrolled with user interaction (user scanning a QR code for example)
    MANUAL_USER = "manual_user"


class ConnectorSyncException(SentryIgnoredException):
    """Base exceptions for errors during sync"""


class BaseConnector[T: "Connector"]:

    connector: T

    def __init__(self, connector: T) -> None:
        self.connector = connector

    def supported_enrollment_methods(self) -> list[EnrollmentMethods]:
        return []

    def stage_view_enrollment(self) -> StageView | None:
        return None

    def stage_view_authentication(self) -> StageView | None:
        return None
