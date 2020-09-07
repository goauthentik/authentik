"""passbook invitation signals"""
from django.core.signals import Signal

invitation_created = Signal(providing_args=["request", "invitation"])
invitation_used = Signal(providing_args=["request", "invitation"])
