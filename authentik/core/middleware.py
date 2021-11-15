"""authentik admin Middleware to impersonate users"""
from logging import Logger
from threading import local
from typing import Callable
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

SESSION_IMPERSONATE_USER = "authentik_impersonate_user"
SESSION_IMPERSONATE_ORIGINAL_USER = "authentik_impersonate_original_user"
LOCAL = local()
RESPONSE_HEADER_ID = "X-authentik-id"
KEY_AUTH_VIA = "auth_via"
KEY_USER = "user"


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
            # Ensure that the user is active, otherwise nothing will work
            request.user.is_active = True

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
            LOCAL.authentik = {
                "request_id": request_id,
                "host": request.get_host(),
            }
        response = self.get_response(request)
        response[RESPONSE_HEADER_ID] = request.request_id
        setattr(response, "ak_context", {})
        if auth_via := LOCAL.authentik.get(KEY_AUTH_VIA, None):
            response.ak_context[KEY_AUTH_VIA] = auth_via
        response.ak_context[KEY_USER] = request.user.username
        for key in list(LOCAL.authentik.keys()):
            del LOCAL.authentik[key]
        return response


# pylint: disable=unused-argument
def structlog_add_request_id(logger: Logger, method_name: str, event_dict: dict):
    """If threadlocal has authentik defined, add request_id to log"""
    if hasattr(LOCAL, "authentik"):
        event_dict.update(LOCAL.authentik)
    return event_dict
