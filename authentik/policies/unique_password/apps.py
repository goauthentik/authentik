"""authentik Unique Password policy app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPoliciesUniquePasswordConfig(ManagedAppConfig):
    name = "authentik.policies.unique_password"
    label = "authentik_policies_unique_password"
    verbose_name = "authentik Policies.Unique Password"
    default = True
