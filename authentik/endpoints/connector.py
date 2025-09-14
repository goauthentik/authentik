from authentik.blueprints import models
from authentik.flows.stage import StageView


class EnrollmentMethods(models.TextChoices):
    # Automatically enrolled through user action
    AUTOMATIC_USER = "automatic_user"
    # Automatically enrolled through connector integration
    AUTOMATIC_API = "automatic_api"
    # Manually enrolled with user interaction (user scanning a QR code for example)
    MANUAL_USER = "manual_user"


class BaseConnector:

    def __init__(self) -> None:
        pass

    def supported_enrollment_methods(self) -> list[EnrollmentMethods]:
        return []

    def stage_view_enrollment(self) -> StageView | None:
        return None

    def stage_view_authentication(self) -> StageView | None:
        return None
