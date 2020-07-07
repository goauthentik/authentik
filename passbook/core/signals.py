"""passbook core signals"""
from django.core.signals import Signal

user_signed_up = Signal(providing_args=["request", "user"])
password_changed = Signal(providing_args=["user", "password"])
