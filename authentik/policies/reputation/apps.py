"""Authentik reputation_policy app config"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikPolicyReputationConfig(AppConfig):
    """Authentik reputation app config"""

    name = "authentik.policies.reputation"
    label = "authentik_policies_reputation"
    verbose_name = "authentik Policies.Reputation"

    def ready(self):
        import_module("authentik.policies.reputation.signals")
