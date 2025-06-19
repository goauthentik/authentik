"""Authentik policy_expiry app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPolicyExpiryConfig(ManagedAppConfig):
    """Authentik policy_expiry app config"""

    name = "authentik.policies.expiry"
    label = "authentik_policies_expiry"
    verbose_name = "authentik Policies.Expiry"
    default = True
