"""passbook audit signal listener"""
from django.contrib.auth.signals import (user_logged_in, user_logged_out,
                                         user_login_failed)
from django.dispatch import receiver

from passbook.audit.models import AuditEntry
from passbook.core.signals import invite_created, invite_used, user_signed_up


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Log successful login"""
    AuditEntry.create(AuditEntry.ACTION_LOGIN, request)

@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Log successfully logout"""
    AuditEntry.create(AuditEntry.ACTION_LOGOUT, request)

@receiver(user_signed_up)
def on_user_signed_up(sender, request, user, **kwargs):
    """Log successfully signed up"""
    AuditEntry.create(AuditEntry.ACTION_SIGN_UP, request)

@receiver(invite_created)
def on_invite_created(sender, request, invite, **kwargs):
    """Log Invite creation"""
    AuditEntry.create(AuditEntry.ACTION_INVITE_CREATED, request, invite_uuid=invite.uuid)

@receiver(invite_used)
def on_invite_used(sender, request, invite, **kwargs):
    """Log Invite usage"""
    AuditEntry.create(AuditEntry.ACTION_INVITE_USED, request, invite_uuid=invite.uuid)

@receiver(user_login_failed)
def on_user_login_failed(sender, request, user, **kwargs):
    """Log failed login attempt"""
    # TODO: Implement sumarizing of signals here for brute-force attempts
    # AuditEntry.create(AuditEntry.ACTION_LOGOUT, request)
    pass
