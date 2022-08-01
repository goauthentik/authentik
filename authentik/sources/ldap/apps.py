"""authentik ldap source config"""
from authentik.blueprints.manager import ManagedAppConfig


class AuthentikSourceLDAPConfig(ManagedAppConfig):
    """Authentik ldap app config"""

    name = "authentik.sources.ldap"
    label = "authentik_sources_ldap"
    verbose_name = "authentik Sources.LDAP"
    default = True

    def reconcile_load_sources_ldap_signals(self):
        """Load sources.ldap signals"""
        self.import_module("authentik.sources.ldap.signals")
