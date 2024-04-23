from typing import TYPE_CHECKING

from googleapiclient.discovery import build

from authentik.enterprise.providers.google.models import GoogleProvider
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient

if TYPE_CHECKING:
    from django.db.models import Model
    from googleapiclient._apis.admin.directory_v1.resources import DirectoryResource


class GoogleSyncClient[TModel: "Model", TSchema: dict](
    BaseOutgoingSyncClient[TModel, TSchema, GoogleProvider]
):

    def __init__(self, provider: GoogleProvider) -> None:
        super().__init__(provider)
        self.directory_service: "DirectoryResource" = build(
            "admin", "directory_v1", credentials=provider.google_credentials()
        )
