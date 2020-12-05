"""authentik policies app config"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikPoliciesConfig(AppConfig):
    """authentik policies app config"""

    name = "authentik.policies"
    label = "authentik_policies"
    verbose_name = "authentik Policies"

    def ready(self):
        import_module("authentik.policies.signals")
