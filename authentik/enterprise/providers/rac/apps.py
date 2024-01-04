"""RAC app config"""
from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseProviderRAC(EnterpriseConfig):
    """authentik enterprise rac app config"""

    name = "authentik.enterprise.providers.rac"
    label = "authentik_providers_rac"
    verbose_name = "authentik Enterprise.Providers.RAC"
    default = True
    mountpoint = ""
    ws_mountpoint = "authentik.enterprise.providers.rac.urls"

    def reconcile_load_rac_signals(self):
        """Load rac signals"""
        self.import_module("authentik.enterprise.providers.rac.signals")
