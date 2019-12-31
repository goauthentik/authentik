"""Passbook reputation_policy app config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookPolicyReputationConfig(AppConfig):
    """Passbook reputation app config"""

    name = "passbook.policies.reputation"
    label = "passbook_policies_reputation"
    verbose_name = "passbook Policies.Reputation"

    def ready(self):
        import_module("passbook.policies.reputation.signals")
