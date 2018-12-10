"""passbook audit signal listener"""
from django.contrib.auth.signals import (user_logged_in, user_logged_out,
                                         user_login_failed)
from django.dispatch import receiver

from passbook.audit.models import AuditEntry


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Log successful login"""
    AuditEntry.create(AuditEntry.ACTION_LOGIN, request)

@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Log successfully logout"""
    AuditEntry.create(AuditEntry.ACTION_LOGOUT, request)

@receiver(user_login_failed)
def on_user_login_failed(sender, request, user, **kwargs):
    """Log failed login attempt"""
    # TODO: Implement sumarizing of signals here for brute-force attempts
    # AuditEntry.create(AuditEntry.ACTION_LOGOUT, request)
    pass
