"""authentik invitation signals"""

from django.dispatch import Signal

# Arguments: request: HttpRequest, invitation: Invitation
invitation_used = Signal()
