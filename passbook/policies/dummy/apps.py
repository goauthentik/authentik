"""Passbook policy dummy app config"""

from django.apps import AppConfig


class PassbookPolicyDummyConfig(AppConfig):
    """Passbook policy_dummy app config"""

    name = "passbook.policies.dummy"
    label = "passbook_policies_dummy"
    verbose_name = "passbook Policies.Dummy"
