"""authentik SAML IdP app config"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikProviderSAMLConfig(AppConfig):
    """authentik SAML IdP app config"""

    name = "authentik.providers.saml"
    label = "authentik_providers_saml"
    verbose_name = "authentik Providers.SAML"
    mountpoint = "application/saml/"

    def ready(self) -> None:
        import_module("authentik.providers.saml.managed")
