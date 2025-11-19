"""authentik events signal listener"""

from importlib import import_module
from typing import Any

from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http import HttpRequest
from rest_framework.request import Request

from authentik.core.models import AuthenticatedSession, User
from authentik.core.signals import login_failed, password_changed
from authentik.events.models import Event, EventAction
from authentik.flows.models import Stage
from authentik.flows.planner import PLAN_CONTEXT_OUTPOST, PLAN_CONTEXT_SOURCE, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.invitation.models import Invitation
from authentik.stages.invitation.signals import invitation_used
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS
from authentik.stages.user_write.signals import user_write
from authentik.tenants.utils import get_current_tenant

SESSION_LOGIN_EVENT = "login_event"
_session_engine = import_module(settings.SESSION_ENGINE)


@receiver(user_logged_in)
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
        if PLAN_CONTEXT_OUTPOST in flow_plan.context:
            # Save outpost context
            kwargs[PLAN_CONTEXT_OUTPOST] = flow_plan.context[PLAN_CONTEXT_OUTPOST]
    event = Event.new(EventAction.LOGIN, **kwargs).from_http(request, user=user)
    request.session[SESSION_LOGIN_EVENT] = event
    request.session.save()


def get_login_event(request_or_session: HttpRequest | AuthenticatedSession | None) -> Event | None:
    """Wrapper to get login event that can be mocked in tests"""
    session = None
    if not request_or_session:
        return None
    if isinstance(request_or_session, HttpRequest | Request):
        session = request_or_session.session
    if isinstance(request_or_session, AuthenticatedSession):
        SessionStore = _session_engine.SessionStore
        session = SessionStore(request_or_session.session.session_key)
    return session.get(SESSION_LOGIN_EVENT, None)


@receiver(user_logged_out)
def on_user_logged_out(sender, request: HttpRequest, user: User, **kwargs):
    """Log successfully logout"""
    # Check if this even comes from the user_login stage's middleware, which will set an extra
    # argument
    event = Event.new(EventAction.LOGOUT)
    if "event_extra" in kwargs:
        event.context.update(kwargs["event_extra"])
    event.from_http(request, user=user)


@receiver(user_write)
def on_user_write(sender, request: HttpRequest, user: User, data: dict[str, Any], **kwargs):
    """Log User write"""
    data["created"] = kwargs.get("created", False)
    Event.new(EventAction.USER_WRITE, **data).from_http(request, user=user)


@receiver(login_failed)
def on_login_failed(
    signal,
    sender,
    credentials: dict[str, str],
    request: HttpRequest,
    stage: Stage | None = None,
    **kwargs,
):
    """Failed Login, authentik custom event"""
    user = User.objects.filter(username=credentials.get("username")).first()
    Event.new(EventAction.LOGIN_FAILED, **credentials, stage=stage, **kwargs).from_http(
        request, user
    )


@receiver(invitation_used)
def on_invitation_used(sender, request: HttpRequest, invitation: Invitation, **_):
    """Log Invitation usage"""
    Event.new(EventAction.INVITE_USED, invitation_uuid=invitation.invite_uuid.hex).from_http(
        request
    )


@receiver(password_changed)
def on_password_changed(sender, user: User, password: str, request: HttpRequest | None, **_):
    """Log password change"""
    Event.new(EventAction.PASSWORD_SET).from_http(request, user=user)


@receiver(post_save, sender=Event)
def event_post_save_notification(sender, instance: Event, **_):
    """Start task to check if any policies trigger an notification on this event"""
    from authentik.events.tasks import event_trigger_dispatch

    event_trigger_dispatch.send(instance.event_uuid)


@receiver(pre_delete, sender=User)
def event_user_pre_delete_cleanup(sender, instance: User, **_):
    """If gdpr_compliance is enabled, remove all the user's events"""
    from authentik.events.tasks import gdpr_cleanup

    if get_current_tenant().gdpr_compliance:
        gdpr_cleanup.send(instance.pk)
