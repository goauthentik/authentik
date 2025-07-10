"""Authentik policy_expiry app config"""

from django.apps import AppConfig


class AuthentikPolicyExpiryConfig(AppConfig):
    """Authentik policy_expiry app config"""

    name = "authentik.policies.expiry"
    label = "authentik_policies_expiry"
    verbose_name = "authentik Policies.Expiry"
