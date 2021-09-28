"""authentik events signal listener"""
from threading import Thread
from typing import Any, Optional

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import User
from authentik.core.signals import password_changed
from authentik.events.models import Event, EventAction
from authentik.events.tasks import event_notification_handler
from authentik.flows.planner import PLAN_CONTEXT_SOURCE, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.invitation.models import Invitation
from authentik.stages.invitation.signals import invitation_used
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS
from authentik.stages.user_write.signals import user_write


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


@receiver(user_logged_in)
# pylint: disable=unused-argument
def on_user_logged_in(sender, request: HttpRequest, user: User, **_):
    """Log successful login"""
    thread = EventNewThread(EventAction.LOGIN, request)
    if SESSION_KEY_PLAN in request.session:
        flow_plan: FlowPlan = request.session[SESSION_KEY_PLAN]
        if PLAN_CONTEXT_SOURCE in flow_plan.context:
            # Login request came from an external source, save it in the context
            thread.kwargs[PLAN_CONTEXT_SOURCE] = flow_plan.context[PLAN_CONTEXT_SOURCE]
        if PLAN_CONTEXT_METHOD in flow_plan.context:
            thread.kwargs[PLAN_CONTEXT_METHOD] = flow_plan.context[PLAN_CONTEXT_METHOD]
            # Save the login method used
            thread.kwargs[PLAN_CONTEXT_METHOD_ARGS] = flow_plan.context.get(
                PLAN_CONTEXT_METHOD_ARGS, {}
            )
    thread.user = user
    thread.run()


@receiver(user_logged_out)
# pylint: disable=unused-argument
def on_user_logged_out(sender, request: HttpRequest, user: User, **_):
    """Log successfully logout"""
    thread = EventNewThread(EventAction.LOGOUT, request)
    thread.user = user
    thread.run()


@receiver(user_write)
# pylint: disable=unused-argument
def on_user_write(sender, request: HttpRequest, user: User, data: dict[str, Any], **kwargs):
    """Log User write"""
    thread = EventNewThread(EventAction.USER_WRITE, request, **data)
    thread.kwargs["created"] = kwargs.get("created", False)
    thread.user = user
    thread.run()


@receiver(user_login_failed)
# pylint: disable=unused-argument
def on_user_login_failed(sender, credentials: dict[str, str], request: HttpRequest, **_):
    """Failed Login"""
    thread = EventNewThread(EventAction.LOGIN_FAILED, request, **credentials)
    thread.run()


@receiver(invitation_used)
# pylint: disable=unused-argument
def on_invitation_used(sender, request: HttpRequest, invitation: Invitation, **_):
    """Log Invitation usage"""
    thread = EventNewThread(
        EventAction.INVITE_USED, request, invitation_uuid=invitation.invite_uuid.hex
    )
    thread.run()


@receiver(password_changed)
# pylint: disable=unused-argument
def on_password_changed(sender, user: User, password: str, **_):
    """Log password change"""
    thread = EventNewThread(EventAction.PASSWORD_SET, None, user=user)
    thread.run()


@receiver(post_save, sender=Event)
# pylint: disable=unused-argument
def event_post_save_notification(sender, instance: Event, **_):
    """Start task to check if any policies trigger an notification on this event"""
    event_notification_handler.delay(instance.event_uuid.hex)
