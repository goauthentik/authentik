"""Enterprise middleware"""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import resolve
from structlog.stdlib import BoundLogger, get_logger

from authentik.common.utils.reflection import class_to_path
from authentik.core.api.users import UserViewSet
from authentik.enterprise.api import LicenseViewSet
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import LicenseUsageStatus
from authentik.flows.views.executor import FlowExecutorView


class EnterpriseMiddleware:
    """Enterprise middleware"""

    get_response: Callable[[HttpRequest], HttpResponse]
    logger: BoundLogger

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.logger = get_logger().bind()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        resolver_match = resolve(request.path_info)
        request.resolver_match = resolver_match
        if not self.is_request_allowed(request):
            self.logger.warning("Refusing request due to expired/invalid license")
            return JsonResponse(
                {
                    "detail": "Request denied due to expired/invalid license.",
                    "code": "denied_license",
                },
                status=400,
            )
        return self.get_response(request)

    def is_request_allowed(self, request: HttpRequest) -> bool:
        """Check if a specific request is allowed"""
        if self.is_request_always_allowed(request):
            return True
        cached_status = LicenseKey.cached_summary()
        if not cached_status:
            return True
        if cached_status.status == LicenseUsageStatus.READ_ONLY:
            return False
        return True

    def is_request_always_allowed(self, request: HttpRequest):
        """Check if a request is always allowed"""
        # Always allow "safe" methods
        if request.method.lower() in ["get", "head", "options", "trace"]:
            return True
        # Always allow requests to manage licenses
        if request.resolver_match._func_path == class_to_path(LicenseViewSet):
            return True
        # Flow executor is mounted as an API path but explicitly allowed
        if request.resolver_match._func_path == class_to_path(FlowExecutorView):
            return True
        # Always allow making changes to users, even in case the license has ben exceeded
        if request.resolver_match._func_path == class_to_path(UserViewSet):
            return True
        # Only apply these restrictions to the API
        if "authentik_api" not in request.resolver_match.app_names:
            return True
        return False
