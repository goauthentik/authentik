from authentik.blueprints import models


class EnrollmentMethods(models.TextChoices):
    AUTOMATIC_USER = "automatic_user"  # Automatically enrolled through user action
    AUTOMATIC_API = "automatic_api"  # Automatically enrolled through connector integration
    MANUAL_USER = "manual_user"  # Manually enrolled


class BaseConnector:

    def __init__(self) -> None:
        pass

    def supported_enrollment_methods(self) -> list[EnrollmentMethods]:
        return []
