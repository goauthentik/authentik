"""passbook sso policy app config"""

from django.apps import AppConfig


class PassbookPoliciesSSOConfig(AppConfig):
    """passbook sso policy app config"""

    name = "passbook.policies.sso"
    label = "passbook_policies_sso"
    verbose_name = "passbook Policies.SSO"
