from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from authentik.admin.utils import system_settings_cache


class SystemSettingsMiddleware:
    """Read the system settings at most once per request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        with system_settings_cache():
            return self.get_response(request)
