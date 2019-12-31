"""Passbook hibp app config"""

from django.apps import AppConfig


class PassbookPolicyHIBPConfig(AppConfig):
    """Passbook hibp app config"""

    name = "passbook.policies.hibp"
    label = "passbook_policies_hibp"
    verbose_name = "passbook Policies.HaveIBeenPwned"
