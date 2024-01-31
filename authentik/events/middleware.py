"""Events middleware"""

from functools import partial
from threading import Thread
from typing import Any, Callable, Optional

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import SuspiciousOperation
from django.db.models import Model
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.http import HttpRequest, HttpResponse
from structlog.stdlib import BoundLogger, get_logger

from authentik.blueprints.v1.importer import excluded_models
from authentik.core.models import Group, User
from authentik.events.models import Event, EventAction, Notification
from authentik.events.utils import model_to_dict
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


def should_log_model(model: Model) -> bool:
    """Return true if operation on `model` should be logged"""
    return model.__class__ not in IGNORED_MODELS


def should_log_m2m(model: Model) -> bool:
    """Return true if m2m operation should be logged"""
    if model.__class__ in [User, Group]:
        return True
    return False


class EventNewThread(Thread):
    """Create Event in background thread"""

    action: str
    request: HttpRequest
    kwargs: dict[str, Any]
    user: Optional[User] = None

    def __init__(self, action: str, request: HttpRequest, user: Optional[User] = None, **kwargs):
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

    def connect(self, request: HttpRequest):
        """Connect signal for automatic logging"""
        self._ensure_fallback_user()
        user = getattr(request, "user", self.anonymous_user)
        if not user.is_authenticated:
            user = self.anonymous_user
        if not hasattr(request, "request_id"):
            return
        post_save.connect(
            partial(self.post_save_handler, user=user, request=request),
            dispatch_uid=request.request_id,
            weak=False,
        )
        pre_delete.connect(
            partial(self.pre_delete_handler, user=user, request=request),
            dispatch_uid=request.request_id,
            weak=False,
        )
        m2m_changed.connect(
            partial(self.m2m_changed_handler, user=user, request=request),
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
        self.connect(request)

        response = self.get_response(request)

        self.disconnect(request)
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
                message=str(exception),
            )
            thread.run()
        elif before_send({}, {"exc_info": (None, exception, None)}) is not None:
            thread = EventNewThread(
                EventAction.SYSTEM_EXCEPTION,
                request,
                message=exception_to_string(exception),
            )
            thread.run()

    # pylint: disable=too-many-arguments
    def post_save_handler(
        self,
        user: User,
        request: HttpRequest,
        sender,
        instance: Model,
        created: bool,
        thread_kwargs: Optional[dict] = None,
        **_,
    ):
        """Signal handler for all object's post_save"""
        if not should_log_model(instance):
            return

        action = EventAction.MODEL_CREATED if created else EventAction.MODEL_UPDATED
        thread = EventNewThread(action, request, user=user, model=model_to_dict(instance))
        thread.kwargs.update(thread_kwargs or {})
        thread.run()

    def pre_delete_handler(self, user: User, request: HttpRequest, sender, instance: Model, **_):
        """Signal handler for all object's pre_delete"""
        if not should_log_model(instance):  # pragma: no cover
            return

        EventNewThread(
            EventAction.MODEL_DELETED,
            request,
            user=user,
            model=model_to_dict(instance),
        ).run()

    def m2m_changed_handler(
        self, user: User, request: HttpRequest, sender, instance: Model, action: str, **_
    ):
        """Signal handler for all object's m2m_changed"""
        if action not in ["pre_add", "pre_remove", "post_clear"]:
            return
        if not should_log_m2m(instance):
            return

        EventNewThread(
            EventAction.MODEL_UPDATED,
            request,
            user=user,
            model=model_to_dict(instance),
        ).run()
