"""Enterprise middleware"""

from collections.abc import Callable
from re import Pattern, compile

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import URLResolver, get_resolver
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.api.users import UserViewSet
from authentik.enterprise.api import LicenseViewSet
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import LicenseUsageStatus
from authentik.flows.views.executor import FlowExecutorView

# Views which are always allowed, even in read-only mode
ALWAYS_ALLOWED_VIEWS = (
    # Always allow requests to manage licenses
    LicenseViewSet,
    # Flow executor is mounted as an API path but explicitly allowed
    FlowExecutorView,
    # Always allow making changes to users, even in case the license has been exceeded
    UserViewSet,
)


def _build_paths(
    resolver: URLResolver, prefix: str, in_api: bool = False
) -> tuple[list[Pattern], list[Pattern]]:
    """Walk the URL tree and return regexes of API mountpoints and of allowed API endpoints"""
    api_paths, allowed_paths = [], []
    for entry in resolver.url_patterns:
        regex = prefix + entry.pattern.regex.pattern.removeprefix("^")
        if isinstance(entry, URLResolver):
            is_api = entry.app_name == "authentik_api"
            if is_api and not in_api:
                api_paths.append(compile(regex))
            sub_api, sub_allowed = _build_paths(entry, regex, in_api or is_api)
            api_paths.extend(sub_api)
            allowed_paths.extend(sub_allowed)
            continue
        view = getattr(entry.callback, "view_class", getattr(entry.callback, "cls", None))
        if in_api and view in ALWAYS_ALLOWED_VIEWS:
            allowed_paths.append(compile(regex))
    return api_paths, allowed_paths


_root = get_resolver()
API_PATHS, ALLOWED_PATHS = _build_paths(_root, _root.pattern.regex.pattern)


class EnterpriseMiddleware:
    """Enterprise middleware"""

    get_response: Callable[[HttpRequest], HttpResponse]
    logger: BoundLogger

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.logger = get_logger().bind()

    def __call__(self, request: HttpRequest) -> HttpResponse:
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
        path = request.path_info
        # Only apply these restrictions to the API
        if not any(api.match(path) for api in API_PATHS):
            return True
        return any(allowed.match(path) for allowed in ALLOWED_PATHS)
