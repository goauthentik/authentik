"""authentik Password policy app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPoliciesPasswordConfig(ManagedAppConfig):
    """authentik Password policy app config"""

    name = "authentik.policies.password"
    label = "authentik_policies_password"
    verbose_name = "authentik Policies.Password"
    default = True
