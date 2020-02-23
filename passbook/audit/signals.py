"""passbook audit signal listener"""
from typing import Dict

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.http import HttpRequest

from passbook.audit.models import Event, EventAction
from passbook.core.models import User
from passbook.core.signals import invitation_created, invitation_used, user_signed_up


@receiver(user_logged_in)
# pylint: disable=unused-argument
def on_user_logged_in(sender, request: HttpRequest, user: User, **_):
    """Log successful login"""
    Event.new(EventAction.LOGIN).from_http(request)


@receiver(user_logged_out)
# pylint: disable=unused-argument
def on_user_logged_out(sender, request: HttpRequest, user: User, **_):
    """Log successfully logout"""
    Event.new(EventAction.LOGOUT).from_http(request)


@receiver(user_login_failed)
# pylint: disable=unused-argument
def on_user_login_failed(
    sender, credentials: Dict[str, str], request: HttpRequest, **_
):
    """Failed Login"""
    Event.new(EventAction.LOGIN_FAILED, **credentials).from_http(request)


@receiver(user_signed_up)
# pylint: disable=unused-argument
def on_user_signed_up(sender, request: HttpRequest, user: User, **_):
    """Log successfully signed up"""
    Event.new(EventAction.SIGN_UP).from_http(request)


@receiver(invitation_created)
# pylint: disable=unused-argument
def on_invitation_created(sender, request: HttpRequest, invitation, **_):
    """Log Invitation creation"""
    Event.new(
        EventAction.INVITE_CREATED, invitation_uuid=invitation.uuid.hex
    ).from_http(request)


@receiver(invitation_used)
# pylint: disable=unused-argument
def on_invitation_used(sender, request: HttpRequest, invitation, **_):
    """Log Invitation usage"""
    Event.new(EventAction.INVITE_USED, invitation_uuid=invitation.uuid.hex).from_http(
        request
    )
