"""passbook invitation signals"""
from django.core.signals import Signal

# Arguments: request: HttpRequest, invitation: Invitation
invitation_created = Signal()
# Arguments: request: HttpRequest, invitation: Invitation
invitation_used = Signal()
