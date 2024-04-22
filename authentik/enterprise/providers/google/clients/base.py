from typing import TYPE_CHECKING

from googleapiclient.discovery import build
from structlog.stdlib import get_logger

from authentik.enterprise.providers.google.models import GoogleProvider

if TYPE_CHECKING:
    from googleapiclient._apis.admin.directory_v1.resources import DirectoryResource


class BaseGoogleSync[Tin, Tout]:

    def __init__(self, provider: GoogleProvider) -> None:
        self.provider = provider
        self.logger = get_logger().bind(provider=provider.name)
        self.directory_service: "DirectoryResource" = build(
            "admin", "directory_v1", credentials=provider.google_credentials()
        )

    def convert_object(self, input: Tin) -> Tout:
        raise NotImplementedError
