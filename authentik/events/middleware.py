"""Events middleware"""

from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from functools import partial
from threading import Thread
from typing import Any

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import SuspiciousOperation
from django.db.models import Model
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.http import HttpRequest, HttpResponse
from structlog.stdlib import BoundLogger, get_logger

from authentik.core.models import Group, User
from authentik.events.models import Event, EventAction, Notification
from authentik.events.utils import model_to_dict
from authentik.lib.models import excluded_models
from authentik.lib.sentry import before_send
from authentik.lib.utils.errors import exception_to_string
from authentik.stages.authenticator_static.models import StaticToken

IGNORED_MODELS = tuple(
    excluded_models()
    + (
        Event,
        Notification,
        StaticToken,
        Session,
    )
)

_CTX_OVERWRITE_USER = ContextVar[User | None]("authentik_events_log_overwrite_user", default=None)
_CTX_IGNORE = ContextVar[bool]("authentik_events_log_ignore", default=False)
_CTX_REQUEST = ContextVar[HttpRequest | None]("authentik_events_log_request", default=None)


def should_log_model(model: Model) -> bool:
    """Return true if operation on `model` should be logged"""
    return model.__class__ not in IGNORED_MODELS


def should_log_m2m(model: Model) -> bool:
    """Return true if m2m operation should be logged"""
    if model.__class__ in [User, Group]:
        return True
    return False


@contextmanager
def audit_overwrite_user(user: User):
    """Overwrite user being logged for model AuditMiddleware. Commonly used
    for example in flows where a pending user is given, but the request is not authenticated yet"""
    _CTX_OVERWRITE_USER.set(user)
    try:
        yield
    finally:
        _CTX_OVERWRITE_USER.set(None)


@contextmanager
def audit_ignore():
    """Ignore model operations in the block. Useful for objects which need to be modified
    but are not excluded (e.g. WebAuthn devices)"""
    _CTX_IGNORE.set(True)
    try:
        yield
    finally:
        _CTX_IGNORE.set(False)


class EventNewThread(Thread):
    """Create Event in background thread"""

    action: str
    request: HttpRequest
    kwargs: dict[str, Any]
    user: User | None = None

    def __init__(self, action: str, request: HttpRequest, user: User | None = None, **kwargs):
        super().__init__()
        self.action = action
        self.request = request
        self.user = user
        self.kwargs = kwargs

    def run(self):
        Event.new(self.action, **self.kwargs).from_http(self.request, user=self.user)


class AuditMiddleware:
    """Register handlers for duration of request-response that log creation/update/deletion
    of models"""

    get_response: Callable[[HttpRequest], HttpResponse]
    anonymous_user: User = None
    logger: BoundLogger

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.logger = get_logger().bind()

    def _ensure_fallback_user(self):
        """Defer fetching anonymous user until we have to"""
        if self.anonymous_user:
            return
        from guardian.shortcuts import get_anonymous_user

        self.anonymous_user = get_anonymous_user()

    def get_user(self, request: HttpRequest) -> User:
        user = _CTX_OVERWRITE_USER.get()
        if user:
            return user
        user = getattr(request, "user", self.anonymous_user)
        if not user.is_authenticated:
            self._ensure_fallback_user()
            return self.anonymous_user
        return user

    def connect(self, request: HttpRequest):
        """Connect signal for automatic logging"""
        if not hasattr(request, "request_id"):
            return
        post_save.connect(
            partial(self.post_save_handler, request=request),
            dispatch_uid=request.request_id,
            weak=False,
        )
        pre_delete.connect(
            partial(self.pre_delete_handler, request=request),
            dispatch_uid=request.request_id,
            weak=False,
        )
        m2m_changed.connect(
            partial(self.m2m_changed_handler, request=request),
            dispatch_uid=request.request_id,
            weak=False,
        )

    def disconnect(self, request: HttpRequest):
        """Disconnect signals"""
        if not hasattr(request, "request_id"):
            return
        post_save.disconnect(dispatch_uid=request.request_id)
        pre_delete.disconnect(dispatch_uid=request.request_id)
        m2m_changed.disconnect(dispatch_uid=request.request_id)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        _CTX_REQUEST.set(request)
        self.connect(request)

        response = self.get_response(request)

        self.disconnect(request)
        _CTX_REQUEST.set(None)
        return response

    def process_exception(self, request: HttpRequest, exception: Exception):
        """Disconnect handlers in case of exception"""
        self.disconnect(request)

        if settings.DEBUG:
            return
        # Special case for SuspiciousOperation, we have a special event action for that
        if isinstance(exception, SuspiciousOperation):
            thread = EventNewThread(
                EventAction.SUSPICIOUS_REQUEST,
                request,
                message=exception_to_string(exception),
            )
            thread.run()
        elif before_send({}, {"exc_info": (None, exception, None)}) is not None:
            thread = EventNewThread(
                EventAction.SYSTEM_EXCEPTION,
                request,
                message=exception_to_string(exception),
            )
            thread.run()

    def post_save_handler(
        self,
        request: HttpRequest,
        sender,
        instance: Model,
        created: bool,
        thread_kwargs: dict | None = None,
        **_,
    ):
        """Signal handler for all object's post_save"""
        if not should_log_model(instance):
            return
        if _CTX_IGNORE.get():
            return
        if request.request_id != _CTX_REQUEST.get().request_id:
            return
        user = self.get_user(request)

        action = EventAction.MODEL_CREATED if created else EventAction.MODEL_UPDATED
        thread = EventNewThread(action, request, user=user, model=model_to_dict(instance))
        thread.kwargs.update(thread_kwargs or {})
        thread.run()

    def pre_delete_handler(self, request: HttpRequest, sender, instance: Model, **_):
        """Signal handler for all object's pre_delete"""
        if not should_log_model(instance):  # pragma: no cover
            return
        if _CTX_IGNORE.get():
            return
        if request.request_id != _CTX_REQUEST.get().request_id:
            return
        user = self.get_user(request)

        EventNewThread(
            EventAction.MODEL_DELETED,
            request,
            user=user,
            model=model_to_dict(instance),
        ).run()

    def m2m_changed_handler(
        self,
        request: HttpRequest,
        sender,
        instance: Model,
        action: str,
        thread_kwargs: dict | None = None,
        **_,
    ):
        """Signal handler for all object's m2m_changed"""
        if action not in ["pre_add", "pre_remove", "post_clear"]:
            return
        if not should_log_m2m(instance):
            return
        if _CTX_IGNORE.get():
            return
        if request.request_id != _CTX_REQUEST.get().request_id:
            return
        user = self.get_user(request)

        EventNewThread(
            EventAction.MODEL_UPDATED,
            request,
            user=user,
            model=model_to_dict(instance),
            **thread_kwargs,
        ).run()
