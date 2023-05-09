"""Enterprise app config"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikEnterpriseConfig(ManagedAppConfig):
    """Enterprise app config"""

    name = "authentik.enterprise"
    label = "authentik_enterprise"
    verbose_name = "authentik Enterprise"
    default = True

    def reconcile_load_enterprise_signals(self):
        """Load enterprise signals"""
        self.import_module("authentik.enterprise.signals")
