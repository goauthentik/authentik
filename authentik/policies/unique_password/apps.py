"""authentik Unique Password policy app config"""

from django.apps import AppConfig


class AuthentikPoliciesUniquePasswordConfig(AppConfig):
    name = "authentik.policies.unique_password"
    label = "authentik_policies_unique_password"
    verbose_name = "authentik Policies.Unique Password"
