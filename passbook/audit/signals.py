"""passbook audit signal listener"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from passbook.audit.models import Event, EventAction
from passbook.core.signals import (invitation_created, invitation_used,
                                   user_signed_up)


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Log successful login"""
    Event.new(EventAction.LOGIN).from_http(request)

@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Log successfully logout"""
    Event.new(EventAction.LOGOUT).from_http(request)

@receiver(user_signed_up)
def on_user_signed_up(sender, request, user, **kwargs):
    """Log successfully signed up"""
    Event.new(EventAction.SIGN_UP).from_http(request)

@receiver(invitation_created)
def on_invitation_created(sender, request, invitation, **kwargs):
    """Log Invitation creation"""
    Event.new(EventAction.INVITE_CREATED, invitation_uuid=invitation.uuid.hex).from_http(request)

@receiver(invitation_used)
def on_invitation_used(sender, request, invitation, **kwargs):
    """Log Invitation usage"""
    Event.new(EventAction.INVITE_USED, invitation_uuid=invitation.uuid.hex).from_http(request)
