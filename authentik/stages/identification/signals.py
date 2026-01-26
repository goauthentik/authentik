"""authentik identification signals"""

from django.dispatch import Signal

# Arguments: request: HttpRequest, uid_field: Value entered by user
identification_failed = Signal()
