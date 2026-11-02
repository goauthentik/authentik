"""InitialPermissions middleware"""

from collections.abc import Callable

from django.db.models import Model
from django.db.models.signals import post_save
from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.status import is_success
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.lib.middleware import SignalMiddleware
from authentik.rbac.endpoint_checks import EndpointChecks, PermissionCheckFailed
from authentik.rbac.endpoints import ALTER_RESPONSE
from authentik.rbac.permissions import assign_initial_permissions

LOGGER = get_logger()


class InitialPermissionsMiddleware(SignalMiddleware):
    """Assign InitialPermissions to objects created during a request"""

    signal_handlers = {post_save: "post_save_handler"}

    def post_save_handler(
        self,
        request: HttpRequest,
        sender: type[Model],
        instance: Model,
        created: bool,
        **_,
    ):
        if not created:
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
