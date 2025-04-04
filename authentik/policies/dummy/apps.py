"""Authentik policy dummy app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPolicyDummyConfig(ManagedAppConfig):
    """Authentik policy_dummy app config"""

    name = "authentik.policies.dummy"
    label = "authentik_policies_dummy"
    verbose_name = "authentik Policies.Dummy"
    default = True
