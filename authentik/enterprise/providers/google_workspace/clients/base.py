from django.db.models import Model
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from google.auth.exceptions import GoogleAuthError, TransportError
from googleapiclient.discovery import build
from googleapiclient.errors import Error, HttpError
from googleapiclient.http import HttpRequest
from httplib2 import HttpLib2Error, HttpLib2ErrorWithResponse

from authentik.common.sync.outgoing import HTTP_CONFLICT
from authentik.common.sync.outgoing.base import SAFE_METHODS, BaseOutgoingSyncClient
from authentik.common.sync.outgoing.exceptions import (
    BadRequestSyncException,
    DryRunRejected,
    NotFoundSyncException,
    ObjectExistsSyncException,
    StopSync,
    TransientSyncException,
)
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider


class GoogleWorkspaceSyncClient[TModel: Model, TConnection: Model, TSchema: dict](
    BaseOutgoingSyncClient[TModel, TConnection, TSchema, GoogleWorkspaceProvider]
):
    """Base client for syncing to google workspace"""

    domains: list

    def __init__(self, provider: GoogleWorkspaceProvider) -> None:
        super().__init__(provider)
        self.directory_service = build(
            "admin",
            "directory_v1",
            cache_discovery=False,
            **provider.google_credentials(),
        )
        self.__prefetch_domains()

    def __prefetch_domains(self):
        self.domains = []
        domains = self._request(self.directory_service.domains().list(customer="my_customer"))
        for domain in domains.get("domains", []):
            domain_name = domain.get("domainName")
            self.domains.append(domain_name)

    def _request(self, request: HttpRequest):
        if self.provider.dry_run and request.method.upper() not in SAFE_METHODS:
            raise DryRunRejected(request.uri, request.method, request.body)
        try:
            response = request.execute()
        except GoogleAuthError as exc:
            if isinstance(exc, TransportError):
                raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
            raise StopSync(exc) from exc
        except HttpLib2Error as exc:
            if isinstance(exc, HttpLib2ErrorWithResponse):
                self._response_handle_status_code(request.body, exc.response.status, exc)
            raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
        except HttpError as exc:
            self._response_handle_status_code(request.body, exc.status_code, exc)
            raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
        except Error as exc:
            raise TransientSyncException(f"Failed to send request: {str(exc)}") from exc
        return response

    def _response_handle_status_code(self, request: dict, status_code: int, root_exc: Exception):
        if status_code == HttpResponseNotFound.status_code:
            raise NotFoundSyncException("Object not found") from root_exc
        if status_code == HTTP_CONFLICT:
            raise ObjectExistsSyncException("Object exists") from root_exc
        if status_code == HttpResponseBadRequest.status_code:
            raise BadRequestSyncException("Bad request", request) from root_exc

    def check_email_valid(self, *emails: str):
        for email in emails:
            if not any(email.endswith(f"@{domain_name}") for domain_name in self.domains):
                raise BadRequestSyncException(f"Invalid email domain: {email}")
