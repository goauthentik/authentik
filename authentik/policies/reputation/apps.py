"""Authentik reputation_policy app config"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikPolicyReputationConfig(ManagedAppConfig):
    """Authentik reputation app config"""

    name = "authentik.policies.reputation"
    label = "authentik_policies_reputation"
    verbose_name = "authentik Policies.Reputation"
    default = True

    def reconcile_load_policies_reputation_signals(self):
        """Load policies.reputation signals"""
        self.import_module("authentik.policies.reputation.signals")

    def reconcile_load_policies_reputation_tasks(self):
        """Load policies.reputation tasks"""
        self.import_module("authentik.policies.reputation.tasks")
