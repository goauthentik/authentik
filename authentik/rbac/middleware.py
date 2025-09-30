"""InitialPermissions middleware"""

from collections.abc import Callable
from contextvars import ContextVar
from functools import partial

from django.db.models import Model
from django.db.models.signals import post_save
from django.http import HttpRequest, HttpResponse

from authentik.core.models import User
from authentik.rbac.permissions import assign_initial_permissions

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
