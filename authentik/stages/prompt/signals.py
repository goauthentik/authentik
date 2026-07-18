"""authentik prompt stage signals"""

from django.dispatch import Signal

# Arguments: password: str, plan_context: dict[str, Any]
password_validate = Signal()
