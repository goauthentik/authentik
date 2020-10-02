"""passbook user_write signals"""
from django.core.signals import Signal

# Arguments: request: HttpRequest, user: User, data: Dict[str, Any]
user_write = Signal()
