"""passbook policies app config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookPoliciesConfig(AppConfig):
    """passbook policies app config"""

    name = "passbook.policies"
    label = "passbook_policies"
    verbose_name = "passbook Policies"

    def ready(self):
        import_module("passbook.policies.signals")
