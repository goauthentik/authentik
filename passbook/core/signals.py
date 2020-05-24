"""passbook core signals"""
from django.core.signals import Signal

user_signed_up = Signal(providing_args=["request", "user"])
invitation_created = Signal(providing_args=["request", "invitation"])
invitation_used = Signal(providing_args=["request", "invitation", "user"])
password_changed = Signal(providing_args=["user", "password"])
