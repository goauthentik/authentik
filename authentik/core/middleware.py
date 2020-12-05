"""authentik admin Middleware to impersonate users"""
from logging import Logger
from threading import local
from typing import Callable
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

SESSION_IMPERSONATE_USER = "authentik_impersonate_user"
SESSION_IMPERSONATE_ORIGINAL_USER = "authentik_impersonate_original_user"
LOCAL = local()


class ImpersonateMiddleware:
    """Middleware to impersonate users"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # No permission checks are done here, they need to be checked before
        # SESSION_IMPERSONATE_USER is set.

        if SESSION_IMPERSONATE_USER in request.session:
            request.user = request.session[SESSION_IMPERSONATE_USER]

        return self.get_response(request)


class RequestIDMiddleware:
    """Add a unique ID to every request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not hasattr(request, "request_id"):
            request_id = uuid4().hex
            setattr(request, "request_id", request_id)
            LOCAL.authentik = {"request_id": request_id}
        response = self.get_response(request)
        response["X-authentik-id"] = request.request_id
        del LOCAL.authentik["request_id"]
        return response


# pylint: disable=unused-argument
def structlog_add_request_id(logger: Logger, method_name: str, event_dict):
    """If threadlocal has authentik defined, add request_id to log"""
    if hasattr(LOCAL, "authentik"):
        event_dict["request_id"] = LOCAL.authentik.get("request_id", "")
    return event_dict
