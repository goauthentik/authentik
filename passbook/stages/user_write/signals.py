"""passbook user_write signals"""
from django.core.signals import Signal

user_write = Signal(providing_args=["request", "user", "data"])
