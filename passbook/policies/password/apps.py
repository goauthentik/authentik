"""passbook Password policy app config"""

from django.apps import AppConfig


class PassbookPoliciesPasswordConfig(AppConfig):
    """passbook Password policy app config"""

    name = "passbook.policies.password"
    label = "passbook_policies_password"
    verbose_name = "passbook Policies.Password"
