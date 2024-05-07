from asyncio import run
from collections.abc import Coroutine
from typing import Any

from django.db.models import Model
from django.http import HttpResponseNotFound
from kiota_abstractions.api_error import APIError
from msgraph import GraphServiceClient

from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
from authentik.lib.sync.outgoing import HTTP_CONFLICT
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient
from authentik.lib.sync.outgoing.exceptions import NotFoundSyncException, ObjectExistsSyncException


class MicrosoftEntraSyncClient[TModel: Model, TConnection: Model, TSchema: dict](
    BaseOutgoingSyncClient[TModel, TConnection, TSchema, MicrosoftEntraProvider]
):
    """Base client for syncing to microsoft entra"""

    domains: list

    def __init__(self, provider: MicrosoftEntraProvider) -> None:
        super().__init__(provider)
        self.client = GraphServiceClient(
            credentials=provider.microsoft_credentials(),
            scopes=["https://graph.microsoft.com/.default"],
        )

    def _request[T](self, request: Coroutine[Any, Any, T]) -> T:
        try:
            return run(request)
        except APIError as exc:
            if exc.response_status_code == HttpResponseNotFound.status_code:
                raise NotFoundSyncException("Object not found") from exc
            if exc.response_status_code == HTTP_CONFLICT:
                raise ObjectExistsSyncException("Object exists") from exc

    # def _request(self, request: HttpRequest):
    #     try:
    #         response = request.execute()
    #     except MicrosoftAuthError as exc:
    #         if isinstance(exc, TransportError):
    #             raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
    #         raise StopSync(exc) from exc
    #     except HttpLib2Error as exc:
    #         if isinstance(exc, HttpLib2ErrorWithResponse):
    #             self._response_handle_status_code(exc.response.status, exc)
    #         raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
    #     except HttpError as exc:
    #         self._response_handle_status_code(exc.status_code, exc)
    #         raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
    #     except Error as exc:
    #         raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
    #     return response
