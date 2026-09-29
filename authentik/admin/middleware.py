from collections.abc import Callable
from typing import Any

from django.http import HttpRequest, HttpResponse
from dramatiq.broker import Broker, MessageProxy
from dramatiq.middleware.middleware import Middleware

from authentik.admin.utils import system_settings_cache


class SystemSettingsCacheRequestMiddleware:
    """Read the system settings at most once per request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        with system_settings_cache():
            return self.get_response(request)


class SystemSettingsCacheTaskMiddleware(Middleware):
    def before_process_message(self, broker: Broker, message: MessageProxy) -> None:
        self.system_settings_cache = system_settings_cache()
        self.system_settings_cache.__enter__()

    def after_process_message(
        self,
        broker: Broker,
        message: MessageProxy,
        *,
        result: Any | None = None,
        exception: BaseException | None = None,
    ) -> None:
        self.system_settings_cache.__exit__(None, None, None)

    def after_skip_message(self, broker: Broker, message: MessageProxy) -> None:
        self.after_process_message(broker, message)
