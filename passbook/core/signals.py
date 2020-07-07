"""passbook core signals"""
from django.core.signals import Signal

password_changed = Signal(providing_args=["user", "password"])
