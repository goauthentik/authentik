"""Authentik reputation_policy app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPolicyReputationConfig(ManagedAppConfig):
    """Authentik reputation app config"""

    name = "authentik.policies.reputation"
    label = "authentik_policies_reputation"
    verbose_name = "authentik Policies.Reputation"
    default = True
