"""Events middleware"""
from functools import partial
from typing import Callable

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import SuspiciousOperation
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete
from django.http import HttpRequest, HttpResponse
from django_otp.plugins.otp_static.models import StaticToken
from guardian.models import UserObjectPermission

from authentik.core.middleware import LOCAL
from authentik.core.models import AuthenticatedSession, User
from authentik.events.models import Event, EventAction, Notification
from authentik.events.signals import EventNewThread
from authentik.events.utils import model_to_dict
from authentik.lib.sentry import before_send
from authentik.lib.utils.errors import exception_to_string

IGNORED_MODELS = [
    Event,
    Notification,
    UserObjectPermission,
    AuthenticatedSession,
    StaticToken,
    Session,
]
if settings.DEBUG:
    from silk.models import Request, Response, SQLQuery

    IGNORED_MODELS += [Request, Response, SQLQuery]
IGNORED_MODELS = tuple(IGNORED_MODELS)


class AuditMiddleware:
    """Register handlers for duration of request-response that log creation/update/deletion
    of models"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Connect signal for automatic logging
        if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
            post_save_handler = partial(self.post_save_handler, user=request.user, request=request)
            pre_delete_handler = partial(
                self.pre_delete_handler, user=request.user, request=request
            )
            post_save.connect(
                post_save_handler,
                dispatch_uid=LOCAL.authentik["request_id"],
                weak=False,
            )
            pre_delete.connect(
                pre_delete_handler,
                dispatch_uid=LOCAL.authentik["request_id"],
                weak=False,
            )

        response = self.get_response(request)

        post_save.disconnect(dispatch_uid=LOCAL.authentik["request_id"])
        pre_delete.disconnect(dispatch_uid=LOCAL.authentik["request_id"])

        return response

    # pylint: disable=unused-argument
    def process_exception(self, request: HttpRequest, exception: Exception):
        """Disconnect handlers in case of exception"""
        post_save.disconnect(dispatch_uid=LOCAL.authentik["request_id"])
        pre_delete.disconnect(dispatch_uid=LOCAL.authentik["request_id"])

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
    # pylint: disable=unused-argument
    def post_save_handler(
        user: User, request: HttpRequest, sender, instance: Model, created: bool, **_
    ):
        """Signal handler for all object's post_save"""
        if isinstance(instance, IGNORED_MODELS):
            return

        action = EventAction.MODEL_CREATED if created else EventAction.MODEL_UPDATED
        EventNewThread(action, request, user=user, model=model_to_dict(instance)).run()

    @staticmethod
    # pylint: disable=unused-argument
    def pre_delete_handler(user: User, request: HttpRequest, sender, instance: Model, **_):
        """Signal handler for all object's pre_delete"""
        if isinstance(instance, IGNORED_MODELS):  # pragma: no cover
            return

        EventNewThread(
            EventAction.MODEL_DELETED,
            request,
            user=user,
            model=model_to_dict(instance),
        ).run()
