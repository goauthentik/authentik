"""authentik Unique Password policy app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterprisePoliciesUniquePasswordConfig(EnterpriseConfig):
    name = "authentik.enterprise.policies.unique_password"
    label = "authentik_policies_unique_password"
    verbose_name = "authentik Enterprise.Policies.Unique Password"
    default = True
