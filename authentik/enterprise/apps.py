"""Enterprise app config"""

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

    def enabled(self):
        """Return true if enterprise is enabled and valid"""
        return self.check_enabled() or settings.TEST

    def check_enabled(self):
        """Actual enterprise check, cached"""
        from authentik.enterprise.license import LicenseKey

        return LicenseKey.cached_summary().status.is_valid
