"""authentik admin Middleware to impersonate users"""

from collections.abc import Callable
from contextvars import ContextVar
from functools import partial
from uuid import uuid4

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.utils.translation import override
from sentry_sdk.api import set_tag
from structlog.contextvars import STRUCTLOG_KEY_PREFIX

SESSION_KEY_IMPERSONATE_USER = "authentik/impersonate/user"
SESSION_KEY_IMPERSONATE_ORIGINAL_USER = "authentik/impersonate/original_user"
RESPONSE_HEADER_ID = "X-authentik-id"
KEY_AUTH_VIA = "auth_via"
KEY_USER = "user"

CTX_REQUEST_ID = ContextVar[str | None](STRUCTLOG_KEY_PREFIX + "request_id", default=None)
CTX_HOST = ContextVar[str | None](STRUCTLOG_KEY_PREFIX + "host", default=None)
CTX_AUTH_VIA = ContextVar[str | None](STRUCTLOG_KEY_PREFIX + KEY_AUTH_VIA, default=None)


def get_user(request):
    if not hasattr(request, "_cached_user"):
        user = None
        if (authenticated_session := request.session.get("authenticatedsession", None)) is not None:
            user = authenticated_session.user
        request._cached_user = user or AnonymousUser()
    return request._cached_user


async def aget_user(request):
    if not hasattr(request, "_cached_user"):
        user = None
        if (
            authenticated_session := await request.session.aget("authenticatedsession", None)
        ) is not None:
            user = authenticated_session.user
        request._cached_user = user or AnonymousUser()
    return request._cached_user


class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not hasattr(request, "session"):
            raise ImproperlyConfigured(
                "The Django authentication middleware requires session "
                "middleware to be installed. Edit your MIDDLEWARE setting to "
                "insert "
                "'authentik.root.middleware.SessionMiddleware' before "
                "'authentik.core.middleware.AuthenticationMiddleware'."
            )
        request.user = SimpleLazyObject(lambda: get_user(request))
        request.auser = partial(aget_user, request)


class ImpersonateMiddleware:
    """Middleware to impersonate users"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # No permission checks are done here, they need to be checked before
        # SESSION_KEY_IMPERSONATE_USER is set.
        locale_to_set = None
        if request.user.is_authenticated:
            locale = request.user.locale(request)
            if locale != "":
                locale_to_set = locale

        if SESSION_KEY_IMPERSONATE_USER in request.session:
            request.user = request.session[SESSION_KEY_IMPERSONATE_USER]
            # Ensure that the user is active, otherwise nothing will work
            request.user.is_active = True

        if locale_to_set:
            with override(locale_to_set):
                return self.get_response(request)
        return self.get_response(request)


class RequestIDMiddleware:
    """Add a unique ID to every request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not hasattr(request, "request_id"):
            request_id = uuid4().hex
            request.request_id = request_id
            CTX_REQUEST_ID.set(request_id)
            CTX_HOST.set(request.get_host())
            set_tag("authentik.request_id", request_id)
        if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
            CTX_AUTH_VIA.set("session")
        else:
            CTX_AUTH_VIA.set("unauthenticated")

        response = self.get_response(request)

        response[RESPONSE_HEADER_ID] = request.request_id
        response.ak_context = {}
        response.ak_context["request_id"] = CTX_REQUEST_ID.get()
        response.ak_context["host"] = CTX_HOST.get()
        response.ak_context[KEY_AUTH_VIA] = CTX_AUTH_VIA.get()
        response.ak_context[KEY_USER] = request.user.username
        return response
