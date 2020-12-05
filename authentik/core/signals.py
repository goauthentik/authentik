"""authentik core signals"""
from django.core.signals import Signal

# Arguments: user: User, password: str
password_changed = Signal()
