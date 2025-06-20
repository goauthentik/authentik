"""authentik Password policy app config"""

from django.apps import AppConfig


class AuthentikPoliciesPasswordConfig(AppConfig):
    """authentik Password policy app config"""

    name = "authentik.policies.password"
    label = "authentik_policies_password"
    verbose_name = "authentik Policies.Password"
