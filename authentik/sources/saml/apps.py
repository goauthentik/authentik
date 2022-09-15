"""Authentik SAML app config"""
from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSourceSAMLConfig(ManagedAppConfig):
    """authentik saml source app config"""

    name = "authentik.sources.saml"
    label = "authentik_sources_saml"
    verbose_name = "authentik Sources.SAML"
    mountpoint = "source/saml/"
    default = True

    def reconcile_load_sources_saml_signals(self):
        """Load sources.saml signals"""
        self.import_module("authentik.sources.saml.signals")
