"""Enterprise app config"""
from functools import lru_cache

from django.conf import settings

from authentik.blueprints.apps import ManagedAppConfig


class EnterpriseConfig(ManagedAppConfig):
    """Base app config for all enterprise apps"""


class AuthentikEnterpriseConfig(EnterpriseConfig):
    """Enterprise app config"""

    name = "authentik.enterprise"
    label = "authentik_enterprise"
    verbose_name = "authentik Enterprise"
    default = True

    def reconcile_global_load_enterprise_signals(self):
        """Load enterprise signals"""
        self.import_module("authentik.enterprise.signals")

    def ready(self) -> None:
        self.check_enabled()
        return super().ready()

    def enabled(self):
        """Return true if enterprise is enabled and valid"""
        return self.check_enabled() or settings.TEST

    @lru_cache()
    def check_enabled(self):
        """Actual enterprise check, cached"""
        from authentik.enterprise.models import LicenseKey

        return LicenseKey.get_total().is_valid()

    def reconcile_install_middleware(self):
        """Install enterprise audit middleware"""
        orig_import = "authentik.events.middleware.AuditMiddleware"
        new_import = "authentik.enterprise.middleware.EnterpriseAuditMiddleware"
        settings.MIDDLEWARE = [new_import if x == orig_import else x for x in settings.MIDDLEWARE]
