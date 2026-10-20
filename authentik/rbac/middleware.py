"""InitialPermissions middleware"""

from collections.abc import Callable
from contextvars import ContextVar
from functools import partial

from django.db.models import Model
from django.db.models.signals import post_save
from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.status import is_success
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.rbac.endpoint_checks import EndpointChecks, PermissionCheckFailed
from authentik.rbac.endpoints import ALTER_RESPONSE
from authentik.rbac.permissions import assign_initial_permissions

LOGGER = get_logger()

_CTX_REQUEST = ContextVar[HttpRequest | None]("authentik_initial_permissions_request", default=None)


class InitialPermissionsMiddleware:
    """Register a handler for duration of request-response that assigns InitialPermissions"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def get_uid(self, request_id: str) -> str:
        return f"InitialPermissionMiddleware-{request_id}"

    def connect(self, request: HttpRequest):
        if not hasattr(request, "request_id"):
            return
        post_save.connect(
            partial(self.post_save_handler, request=request),
            dispatch_uid=self.get_uid(request.request_id),
            weak=False,
        )

    def disconnect(self, request: HttpRequest):
        if not hasattr(request, "request_id"):
            return
        post_save.disconnect(dispatch_uid=self.get_uid(request.request_id))

    def __call__(self, request: HttpRequest) -> HttpResponse:
        _CTX_REQUEST.set(request)
        self.connect(request)

        response = self.get_response(request)

        self.disconnect(request)
        _CTX_REQUEST.set(None)
        return response

    def process_exception(self, request: HttpRequest, exception: Exception):
        self.disconnect(request)

    def post_save_handler(
        self,
        request: HttpRequest,
        instance: Model,
        created: bool,
        **_,
    ):
        if not created:
            return
        current_request = _CTX_REQUEST.get()
        if current_request is None or request.request_id != current_request.request_id:
            return
        user: User = request.user
        if not user or user.is_anonymous:
            return
        assign_initial_permissions(user, instance)


class AlterResponseMiddleware:
    """Lets the permission check of an endpoint change the data it responds with"""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        # alter_response only changes API data; fail closed rather than skip it silently
        if (
            not isinstance(response, Response)
            and is_success(response.status_code)
            and getattr(request, "user", None) is not None
            and EndpointChecks.for_request(request).defines(ALTER_RESPONSE)
        ):
            LOGGER.warning("alter_response cannot change this response", path=request.path)
            failure = PermissionCheckFailed()
            return JsonResponse({"detail": failure.detail}, status=failure.status_code)
        return response

    def process_template_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        api_request = (getattr(response, "renderer_context", None) or {}).get("request")
        if api_request is None or not is_success(response.status_code) or response.data is None:
            return response
        try:
            response.data = EndpointChecks.for_request(api_request).alter_response(response.data)
        except APIException as exc:
            response.data = {"detail": exc.detail}
            response.status_code = exc.status_code
        return response
