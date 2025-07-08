"""Authentik policy dummy app config"""

from django.apps import AppConfig


class AuthentikPolicyDummyConfig(AppConfig):
    """Authentik policy_dummy app config"""

    name = "authentik.policies.dummy"
    label = "authentik_policies_dummy"
    verbose_name = "authentik Policies.Dummy"
