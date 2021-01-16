"""Events middleware"""
from functools import partial
from typing import Callable

from django.contrib.auth.models import User
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete
from django.http import HttpRequest, HttpResponse
from guardian.models import UserObjectPermission

from authentik.core.middleware import LOCAL
from authentik.events.models import Event, EventAction, Notification
from authentik.events.signals import EventNewThread
from authentik.events.utils import model_to_dict


class AuditMiddleware:
    """Register handlers for duration of request-response that log creation/update/deletion
    of models"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Connect signal for automatic logging
        if hasattr(request, "user") and getattr(
            request.user, "is_authenticated", False
        ):
            post_save_handler = partial(
                self.post_save_handler, user=request.user, request=request
            )
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
        """Unregister handlers in case of exception"""
        post_save.disconnect(dispatch_uid=LOCAL.authentik["request_id"])
        pre_delete.disconnect(dispatch_uid=LOCAL.authentik["request_id"])

    @staticmethod
    # pylint: disable=unused-argument
    def post_save_handler(
        user: User, request: HttpRequest, sender, instance: Model, created: bool, **_
    ):
        """Signal handler for all object's post_save"""
        if isinstance(instance, (Event, Notification, UserObjectPermission)):
            return

        action = EventAction.MODEL_CREATED if created else EventAction.MODEL_UPDATED
        EventNewThread(action, request, user=user, model=model_to_dict(instance)).run()

    @staticmethod
    # pylint: disable=unused-argument
    def pre_delete_handler(
        user: User, request: HttpRequest, sender, instance: Model, **_
    ):
        """Signal handler for all object's pre_delete"""
        if isinstance(instance, (Event, Notification, UserObjectPermission)):
            return

        EventNewThread(
            EventAction.MODEL_DELETED,
            request,
            user=user,
            model=model_to_dict(instance),
        ).run()
