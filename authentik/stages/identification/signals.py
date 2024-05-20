"""authentik identification signals"""

from django.core.signals import Signal

# Arguments: request: HttpRequest, uid_field: Value entered by user
identification_failed = Signal()
