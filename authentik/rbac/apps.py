"""authentik rbac app config"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikRBACConfig(ManagedAppConfig):
    """authentik rbac app config"""

    name = "authentik.rbac"
    label = "authentik_rbac"
    verbose_name = "authentik RBAC"
    default = True

    def reconcile_load_rbac_signals(self):
        """Load rbac signals"""
        self.import_module("authentik.rbac.signals")
