"""authentik user_write signals"""

from django.core.signals import Signal

# Arguments: request: HttpRequest, user: User, data: dict[str, Any], created: bool
user_write = Signal()
