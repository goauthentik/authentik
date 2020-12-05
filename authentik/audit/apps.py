"""authentik audit app"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikAuditConfig(AppConfig):
    """authentik audit app"""

    name = "authentik.audit"
    label = "authentik_audit"
    verbose_name = "authentik Audit"
    mountpoint = "audit/"

    def ready(self):
        import_module("authentik.audit.signals")
