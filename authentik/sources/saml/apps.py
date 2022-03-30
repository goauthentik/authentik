"""Authentik SAML app config"""

from importlib import import_module

from django.apps import AppConfig


class AuthentikSourceSAMLConfig(AppConfig):
    """authentik saml source app config"""

    name = "authentik.sources.saml"
    label = "authentik_sources_saml"
    verbose_name = "authentik Sources.SAML"
    mountpoint = "source/saml/"

    def ready(self):
        import_module("authentik.sources.saml.signals")
