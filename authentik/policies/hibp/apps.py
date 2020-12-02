"""Authentik hibp app config"""

from django.apps import AppConfig


class AuthentikPolicyHIBPConfig(AppConfig):
    """Authentik hibp app config"""

    name = "authentik.policies.hibp"
    label = "authentik_policies_hibp"
    verbose_name = "authentik Policies.HaveIBeenPwned"
