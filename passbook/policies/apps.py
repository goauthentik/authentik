"""passbook policies app config"""
from importlib import import_module

from django.apps import AppConfig


class PassbookPoliciesConfig(AppConfig):
    """passbook policies app config"""

    name = "passbook.policies"
    label = "passbook_policies"
    verbose_name = "passbook Policies"

    def ready(self):
        """Load source_types from config file"""
        import_module("passbook.policies.signals")
