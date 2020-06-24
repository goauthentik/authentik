"""Passbook SAML app config"""

from importlib import import_module

from django.apps import AppConfig


class PassbookSourceSAMLConfig(AppConfig):
    """passbook saml_idp app config"""

    name = "passbook.sources.saml"
    label = "passbook_sources_saml"
    verbose_name = "passbook Sources.SAML"
    mountpoint = "source/saml/"

    def ready(self):
        import_module("passbook.sources.saml.signals")
