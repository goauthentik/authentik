"""Enterprise app config"""
from authentik.blueprints.apps import ManagedAppConfig


class EnterpriseConfig(ManagedAppConfig):
    """Base app config for all enterprise apps"""


class AuthentikEnterpriseConfig(EnterpriseConfig):
    """Enterprise app config"""

    name = "authentik.enterprise"
    label = "authentik_enterprise"
    verbose_name = "authentik Enterprise"
    default = True

    def reconcile_load_enterprise_signals(self):
        """Load enterprise signals"""
        self.import_module("authentik.enterprise.signals")
