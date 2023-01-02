"""authentik events signal listener"""
from typing import Any, Optional

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import User
from authentik.core.signals import login_failed, password_changed
from authentik.events.models import Event, EventAction
from authentik.events.tasks import event_notification_handler, gdpr_cleanup
from authentik.flows.models import Stage
from authentik.flows.planner import PLAN_CONTEXT_SOURCE, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.invitation.models import Invitation
from authentik.stages.invitation.signals import invitation_used
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS
from authentik.stages.user_write.signals import user_write

SESSION_LOGIN_EVENT = "login_event"


@receiver(user_logged_in)
# pylint: disable=unused-argument
def on_user_logged_in(sender, request: HttpRequest, user: User, **_):
    """Log successful login"""
    kwargs = {}
    if SESSION_KEY_PLAN in request.session:
        flow_plan: FlowPlan = request.session[SESSION_KEY_PLAN]
        if PLAN_CONTEXT_SOURCE in flow_plan.context:
            # Login request came from an external source, save it in the context
            kwargs[PLAN_CONTEXT_SOURCE] = flow_plan.context[PLAN_CONTEXT_SOURCE]
        if PLAN_CONTEXT_METHOD in flow_plan.context:
            # Save the login method used
            kwargs[PLAN_CONTEXT_METHOD] = flow_plan.context[PLAN_CONTEXT_METHOD]
            kwargs[PLAN_CONTEXT_METHOD_ARGS] = flow_plan.context.get(PLAN_CONTEXT_METHOD_ARGS, {})
    event = Event.new(EventAction.LOGIN, **kwargs).from_http(request, user=user)
    request.session[SESSION_LOGIN_EVENT] = event


def get_login_event(request: HttpRequest) -> Optional[Event]:
    """Wrapper to get login event that can be mocked in tests"""
    return request.session.get(SESSION_LOGIN_EVENT, None)


@receiver(user_logged_out)
# pylint: disable=unused-argument
def on_user_logged_out(sender, request: HttpRequest, user: User, **_):
    """Log successfully logout"""
    Event.new(EventAction.LOGOUT).from_http(request, user=user)


@receiver(user_write)
# pylint: disable=unused-argument
def on_user_write(sender, request: HttpRequest, user: User, data: dict[str, Any], **kwargs):
    """Log User write"""
    data["created"] = kwargs.get("created", False)
    Event.new(EventAction.USER_WRITE, **data).from_http(request, user=user)


@receiver(login_failed)
# pylint: disable=unused-argument
def on_login_failed(
    signal,
    sender,
    credentials: dict[str, str],
    request: HttpRequest,
    stage: Optional[Stage] = None,
    **kwargs,
):
    """Failed Login, authentik custom event"""
    Event.new(EventAction.LOGIN_FAILED, **credentials, stage=stage, **kwargs).from_http(request)


@receiver(invitation_used)
# pylint: disable=unused-argument
def on_invitation_used(sender, request: HttpRequest, invitation: Invitation, **_):
    """Log Invitation usage"""
    Event.new(EventAction.INVITE_USED, invitation_uuid=invitation.invite_uuid.hex).from_http(
        request
    )


@receiver(password_changed)
# pylint: disable=unused-argument
def on_password_changed(sender, user: User, password: str, **_):
    """Log password change"""
    Event.new(EventAction.PASSWORD_SET).from_http(None, user=user)


@receiver(post_save, sender=Event)
# pylint: disable=unused-argument
def event_post_save_notification(sender, instance: Event, **_):
    """Start task to check if any policies trigger an notification on this event"""
    event_notification_handler.delay(instance.event_uuid.hex)


@receiver(pre_delete, sender=User)
# pylint: disable=unused-argument
def event_user_pre_delete_cleanup(sender, instance: User, **_):
    """If gdpr_compliance is enabled, remove all the user's events"""
    gdpr_cleanup.delay(instance.pk)
