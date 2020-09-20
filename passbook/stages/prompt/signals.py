"""passbook prompt stage signals"""
from django.core.signals import Signal

password_validate = Signal(providing_args=["password", "plan_context"])
