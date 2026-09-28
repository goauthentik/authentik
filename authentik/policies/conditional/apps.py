"""authentik conditional policy app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPolicyConditionalConfig(ManagedAppConfig):
    """authentik conditional policy app config"""

    name = "authentik.policies.conditional"
    label = "authentik_policies_conditional"
    verbose_name = "authentik Policies.Conditional"
    default = True
