from django.db.models import Model
from django.http import HttpResponseNotFound
from google.auth.exceptions import GoogleAuthError, TransportError
from googleapiclient.discovery import build
from googleapiclient.errors import Error
from googleapiclient.http import HttpRequest
from httplib2 import HttpLib2Error, HttpLib2ErrorWithResponse

from authentik.enterprise.providers.google.models import GoogleProvider
from authentik.lib.sync.outgoing import HTTP_CONFLICT
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient
from authentik.lib.sync.outgoing.exceptions import (
    NotFoundSyncException,
    ObjectExistsException,
    StopSync,
    TransientSyncException,
)


class GoogleSyncClient[TModel: Model, TSchema: dict](
    BaseOutgoingSyncClient[TModel, TSchema, GoogleProvider]
):
    """Base client for syncing to google workspace"""

    def __init__(self, provider: GoogleProvider) -> None:
        super().__init__(provider)
        self.directory_service = build(
            "admin",
            "directory_v1",
            credentials=provider.google_credentials(),
            cache_discovery=False,
        )

    def _request(self, request: HttpRequest):
        try:
            response = request.execute()
        except GoogleAuthError as exc:
            if isinstance(exc, TransportError):
                raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
            raise StopSync(exc) from exc
        except HttpLib2Error as exc:
            if (
                isinstance(exc, HttpLib2ErrorWithResponse)
                and exc.response.status == HttpResponseNotFound.status_code
            ):
                raise NotFoundSyncException("Object not found") from exc
            if isinstance(exc, HttpLib2ErrorWithResponse) and exc.response.status == HTTP_CONFLICT:
                raise ObjectExistsException("Object exists") from exc
            raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
        except Error as exc:
            raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
        return response
