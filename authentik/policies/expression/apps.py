"""Authentik policy_expression app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPolicyExpressionConfig(ManagedAppConfig):
    """Authentik policy_expression app config"""

    name = "authentik.policies.expression"
    label = "authentik_policies_expression"
    verbose_name = "authentik Policies.Expression"
    default = True
