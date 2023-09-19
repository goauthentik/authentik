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
from guardian.models import UserObjectPermission

from authentik.core.models import (
    AuthenticatedSession,
    Group,
    PropertyMapping,
    Provider,
    Source,
    User,
    UserSourceConnection,
)
from authentik.events.models import Event, EventAction, Notification
from authentik.events.utils import model_to_dict
from authentik.flows.models import FlowToken, Stage
from authentik.lib.sentry import before_send
from authentik.lib.utils.errors import exception_to_string
from authentik.outposts.models import OutpostServiceConnection
from authentik.policies.models import Policy, PolicyBindingModel
from authentik.providers.oauth2.models import AccessToken, AuthorizationCode, RefreshToken
from authentik.providers.scim.models import SCIMGroup, SCIMUser
from authentik.stages.authenticator_static.models import StaticToken

IGNORED_MODELS = (
    Event,
    Notification,
    UserObjectPermission,
    AuthenticatedSession,
    StaticToken,
    Session,
    FlowToken,
    Provider,
    Source,
    PropertyMapping,
    UserSourceConnection,
    Stage,
    OutpostServiceConnection,
    Policy,
    PolicyBindingModel,
    AuthorizationCode,
    AccessToken,
    RefreshToken,
    SCIMUser,
    SCIMGroup,
)


def should_log_model(model: Model) -> bool:
    """Return true if operation on `model` should be logged"""
    if model.__module__.startswith("silk"):
        return False
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

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def connect(self, request: HttpRequest):
        """Connect signal for automatic logging"""
        if not hasattr(request, "user"):
            return
        if not getattr(request.user, "is_authenticated", False):
            return
        if not hasattr(request, "request_id"):
            return
        post_save_handler = partial(self.post_save_handler, user=request.user, request=request)
        pre_delete_handler = partial(self.pre_delete_handler, user=request.user, request=request)
        m2m_changed_handler = partial(self.m2m_changed_handler, user=request.user, request=request)
        post_save.connect(
            post_save_handler,
            dispatch_uid=request.request_id,
            weak=False,
        )
        pre_delete.connect(
            pre_delete_handler,
            dispatch_uid=request.request_id,
            weak=False,
        )
        m2m_changed.connect(
            m2m_changed_handler,
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

    @staticmethod
    def post_save_handler(
        user: User, request: HttpRequest, sender, instance: Model, created: bool, **_
    ):
        """Signal handler for all object's post_save"""
        if not should_log_model(instance):
            return

        action = EventAction.MODEL_CREATED if created else EventAction.MODEL_UPDATED
        EventNewThread(action, request, user=user, model=model_to_dict(instance)).run()

    @staticmethod
    def pre_delete_handler(user: User, request: HttpRequest, sender, instance: Model, **_):
        """Signal handler for all object's pre_delete"""
        if not should_log_model(instance):  # pragma: no cover
            return

        EventNewThread(
            EventAction.MODEL_DELETED,
            request,
            user=user,
            model=model_to_dict(instance),
        ).run()

    @staticmethod
    def m2m_changed_handler(
        user: User, request: HttpRequest, sender, instance: Model, action: str, **_
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
