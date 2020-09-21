"""passbook audit signal listener"""
from threading import Thread
from typing import Any, Dict, Optional

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.http import HttpRequest

from passbook.audit.models import Event, EventAction
from passbook.core.models import User
from passbook.stages.invitation.models import Invitation
from passbook.stages.invitation.signals import invitation_created, invitation_used
from passbook.stages.user_write.signals import user_write


class EventNewThread(Thread):
    """Create Event in background thread"""

    action: str
    request: HttpRequest
    kwargs: Dict[str, Any]
    user: Optional[User] = None

    def __init__(self, action: str, request: HttpRequest, **kwargs):
        super().__init__()
        self.action = action
        self.request = request
        self.kwargs = kwargs

    def run(self):
        Event.new(self.action, **self.kwargs).from_http(self.request, user=self.user)


@receiver(user_logged_in)
# pylint: disable=unused-argument
def on_user_logged_in(sender, request: HttpRequest, user: User, **_):
    """Log successful login"""
    thread = EventNewThread(EventAction.LOGIN, request)
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
def on_user_write(sender, request: HttpRequest, user: User, data: Dict[str, Any], **_):
    """Log User write"""
    thread = EventNewThread("stages/user_write", request, **data)
    thread.user = user
    thread.run()


@receiver(user_login_failed)
# pylint: disable=unused-argument
def on_user_login_failed(
    sender, credentials: Dict[str, str], request: HttpRequest, **_
):
    """Failed Login"""
    thread = EventNewThread(EventAction.LOGIN_FAILED, request, **credentials)
    thread.run()


@receiver(invitation_created)
# pylint: disable=unused-argument
def on_invitation_created(sender, request: HttpRequest, invitation: Invitation, **_):
    """Log Invitation creation"""
    thread = EventNewThread(
        EventAction.INVITE_CREATED, request, invitation_uuid=invitation.invite_uuid.hex
    )
    thread.run()


@receiver(invitation_used)
# pylint: disable=unused-argument
def on_invitation_used(sender, request: HttpRequest, invitation: Invitation, **_):
    """Log Invitation usage"""
    thread = EventNewThread(
        EventAction.INVITE_USED, request, invitation_uuid=invitation.invite_uuid.hex
    )
    thread.run()
